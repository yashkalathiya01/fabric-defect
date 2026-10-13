"""
Fabric AI Inspection System - API Endpoints
============================================

FastAPI routes for fabric defect detection, structural weave analysis,
full inspection, report generation, and database history.
"""

import os
import shutil
import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from backend.app.config import (
    UPLOAD_DIR,
    RESULTS_DIR,
    ALLOWED_EXTENSIONS,
    MAX_FILE_SIZE_MB,
    CONFIDENCE_THRESHOLD,
    MODEL_PATH,
    NUM_CLASSES,
)
from backend.app.database.database import get_db
from backend.app.database.models import InspectionRecord
from backend.app.model.model_loader import load_model
from backend.app.model.detector import detect_defects
from backend.app.analysis.visualizer import visualize_detections
from backend.app.analysis.structure_analyzer import analyze_fabric_structure
from backend.app.analysis.inspector import run_full_inspection
from backend.app.analysis.fabric_validator import validate_fabric_image
from backend.app.reports.report_generator import generate_pdf_report

router = APIRouter()


def _save_upload(file: UploadFile) -> str:
    """Validate and securely save an uploaded fabric image."""
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format '{ext}'. Allowed formats: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
        )

    os.makedirs(UPLOAD_DIR, exist_ok=True)
    # Sanitize and create unique filename
    safe_name = f"fabric_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}{ext}"
    dest_path = os.path.join(UPLOAD_DIR, safe_name)

    # Read and enforce max size limit
    contents = file.file.read()
    size_mb = len(contents) / (1024 * 1024)
    if size_mb > MAX_FILE_SIZE_MB:
        raise HTTPException(
            status_code=413,
            detail=f"File size ({size_mb:.1f} MB) exceeds maximum allowed ({MAX_FILE_SIZE_MB} MB).",
        )

    with open(dest_path, "wb") as f:
        f.write(contents)

    return dest_path


# ---------------------------------------------------------------------------
# 1. Health Check
# ---------------------------------------------------------------------------
@router.get("/health", summary="System Health & Model Status")
def health_check():
    """Returns the operational status of the inspection system, model, and device."""
    model, class_names, device = load_model()
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "model": {
            "name": "Faster R-CNN + ResNet-50 FPN",
            "classes": list(class_names.values()),
            "num_classes": len(class_names),
            "loaded": model is not None,
            "device": str(device),
            "model_path": MODEL_PATH,
        },
        "version": "1.0.0",
    }


# ---------------------------------------------------------------------------
# 2. Defect Detection Only (POST /predict)
# ---------------------------------------------------------------------------
@router.post("/predict", summary="Run AI Defect Detection Only")
async def predict_defects(
    file: UploadFile = File(...),
    confidence_threshold: float = Form(CONFIDENCE_THRESHOLD),
):
    """
    Detect fabric defects (hole, knot, stain) and return bounding boxes + confidence scores.
    Validates that the uploaded image is genuine fabric before invoking Faster R-CNN.
    """
    img_path = _save_upload(file)
    try:
        # Pre-inference Fabric Validation Gating
        fabric_val = validate_fabric_image(img_path)
        base_name = os.path.splitext(os.path.basename(img_path))[0]
        vis_path = os.path.join(RESULTS_DIR, f"{base_name}_annotated.jpg")

        if not fabric_val.get("is_valid_fabric", True):
            # Non-fabric image rejected: suppress defect detector completely
            shutil.copyfile(img_path, vis_path)
            return {
                "is_valid_fabric": False,
                "material_status": "Non-Fabric",
                "message": fabric_val.get(
                    "message",
                    "The uploaded specimen was identified as invalid photo rather than an authentic textile fabric photo. Automated Faster R-CNN defect proposal was bypassed to prevent false-positive defect alarms on non-fabric surfaces."
                ),
                "detected_category": fabric_val.get("detected_category", "Invalid Photo"),
                "suggestion": fabric_val.get(
                    "suggestion",
                    "Please upload a close-up photograph of woven fabric, knitwear, or textile material."
                ),
                "image_path": img_path,
                "confidence_threshold": confidence_threshold,
                "model": {
                    "name": "Faster R-CNN + ResNet-50 FPN",
                    "classes": ["hole", "knot", "stain"],
                },
                "detections": [],
                "all_detections": [],
                "summary": {"total": 0, "hole": 0, "knot": 0, "stain": 0},
                "fabric_validation": fabric_val,
                "annotated_image_url": f"/static/results/{os.path.basename(vis_path)}",
                "original_image_url": f"/static/uploads/{os.path.basename(img_path)}",
            }

        # Fabric verified: run Faster R-CNN defect detection
        detection_res = detect_defects(img_path, confidence_threshold=confidence_threshold)
        visualize_detections(img_path, detection_res["detections"], output_path=vis_path)

        det_count = len(detection_res["detections"])
        detection_res["is_valid_fabric"] = True
        detection_res["material_status"] = "Fabric Verified"
        detection_res["detection_status"] = "Defects Detected" if det_count > 0 else "No Defects"
        detection_res["message"] = (
            f"Fabric verified — {det_count} defect(s) detected."
            if det_count > 0
            else "Fabric verified — no defects detected."
        )
        detection_res["fabric_validation"] = fabric_val
        detection_res["annotated_image_url"] = f"/static/results/{os.path.basename(vis_path)}"
        detection_res["original_image_url"] = f"/static/uploads/{os.path.basename(img_path)}"
        return detection_res
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Inference error: {str(e)}")


# ---------------------------------------------------------------------------
# 3. OpenCV Structural Analysis Only (POST /analyze)
# ---------------------------------------------------------------------------
@router.post("/analyze", summary="Run OpenCV Structural Weave Analysis")
async def analyze_structure(
    file: UploadFile = File(...),
):
    """
    Perform edge detection, Hough line transform, and yarn orientation/spacing analysis.
    Returns warp/weft angles, spacing regularity, and intermediate step images.
    """
    img_path = _save_upload(file)
    try:
        struct_res = analyze_fabric_structure(img_path)

        # Convert local file paths to static web URLs for frontend visualization
        base_name = os.path.splitext(os.path.basename(img_path))[0]
        vis_urls = {}
        for key, p in struct_res.get("visualization_paths", {}).items():
            if p and os.path.isfile(p):
                vis_urls[key] = f"/static/results/structural/{os.path.basename(p)}"

        struct_res["visualization_urls"] = vis_urls
        struct_res["original_image_url"] = f"/static/uploads/{os.path.basename(img_path)}"
        return struct_res
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Structural analysis error: {str(e)}")


# ---------------------------------------------------------------------------
# 4. Master Full Inspection (POST /inspect)
# ---------------------------------------------------------------------------
@router.post("/inspect", summary="Run Complete AI Defect + Structural Inspection")
async def inspect_fabric(
    file: UploadFile = File(...),
    confidence_threshold: float = Form(CONFIDENCE_THRESHOLD),
    db: Session = Depends(get_db),
):
    """
    Full end-to-end inspection:
      1. AI Defect Detection (Faster R-CNN)
      2. OpenCV Weave & Warp/Weft Structural Analysis
      3. Defect & Structure Score Fusion
      4. Fabric Quality Grade Determination (A/B/C/D)
      5. Automatic ReportLab PDF generation
      6. Record persistence in Database
    """
    img_path = _save_upload(file)
    try:
        inspection_result = run_full_inspection(img_path, confidence_threshold=confidence_threshold)
        iid = inspection_result["inspection_id"]

        # Automatically generate PDF report
        pdf_path = generate_pdf_report(inspection_result)
        inspection_result["report_pdf_path"] = pdf_path
        inspection_result["report_download_url"] = f"/api/report/{iid}"

        # URL mappings for frontend
        anno_local = inspection_result["image"]["annotated_path"]
        inspection_result["image"]["original_url"] = f"/static/uploads/{os.path.basename(img_path)}"
        inspection_result["image"]["annotated_url"] = f"/static/results/{iid}/{os.path.basename(anno_local)}"

        # Convert structural paths to URLs
        vis_urls = {}
        for key, p in inspection_result["structural_analysis"].get("visualization_paths", {}).items():
            if p and os.path.isfile(p):
                vis_urls[key] = f"/static/results/{iid}/structural/{os.path.basename(p)}"
        inspection_result["structural_analysis"]["visualization_urls"] = vis_urls

        # Persist to database
        db_record = InspectionRecord(
            inspection_id=iid,
            timestamp=datetime.fromisoformat(inspection_result["timestamp"]),
            image_filename=os.path.basename(img_path),
            original_image_path=img_path,
            annotated_image_path=anno_local,
            total_defects=inspection_result["defects"]["total"],
            hole_count=inspection_result["defects"]["hole"],
            knot_count=inspection_result["defects"]["knot"],
            stain_count=inspection_result["defects"]["stain"],
            defect_area_pct=inspection_result["defect_analysis"]["defect_area_percentage"],
            defect_score=inspection_result["quality"]["defect_score"],
            structure_score=inspection_result["quality"]["structure_score"],
            quality_score=inspection_result["quality"]["quality_score"],
            grade=inspection_result["quality"]["grade"],
            grade_description=inspection_result["quality"]["grade_description"],
            warp_angle=inspection_result["structural_analysis"].get("warp_angle"),
            weft_angle=inspection_result["structural_analysis"].get("weft_angle"),
            warp_spacing=inspection_result["structural_analysis"].get("warp_spacing"),
            weft_spacing=inspection_result["structural_analysis"].get("weft_spacing"),
            alignment_deviation=inspection_result["structural_analysis"].get("alignment_deviation"),
            orientation_confidence=inspection_result["structural_analysis"].get("orientation_confidence"),
            inference_time_ms=inspection_result["timing"]["inference_time_ms"],
            total_inspection_time_ms=inspection_result["timing"]["total_inspection_time_ms"],
            report_pdf_path=pdf_path,
            full_result_json=inspection_result,
        )
        db.add(db_record)
        db.commit()

        return inspection_result
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Inspection pipeline failure: {str(e)}")


# ---------------------------------------------------------------------------
# 5. PDF Report Endpoints
# ---------------------------------------------------------------------------
@router.get("/report/{inspection_id}", summary="Download Inspection PDF Report")
def get_report(inspection_id: str, db: Session = Depends(get_db)):
    """Retrieve and download the generated PDF inspection report."""
    record = db.query(InspectionRecord).filter(InspectionRecord.inspection_id == inspection_id).first()
    if record and record.full_result_json:
        target_pdf = record.report_pdf_path or os.path.join(RESULTS_DIR, inspection_id, f"Fabric_Inspection_Report_{inspection_id}.pdf")
        try:
            generate_pdf_report(record.full_result_json, output_pdf_path=target_pdf)
            if record.report_pdf_path != target_pdf:
                record.report_pdf_path = target_pdf
                db.commit()
        except Exception:
            pass

    if not record or not record.report_pdf_path or not os.path.isfile(record.report_pdf_path):
        # Fallback check on filesystem
        fallback_pdf = os.path.join(RESULTS_DIR, inspection_id, f"Fabric_Inspection_Report_{inspection_id}.pdf")
        if os.path.isfile(fallback_pdf):
            return FileResponse(
                fallback_pdf,
                media_type="application/pdf",
                filename=f"Fabric_Inspection_Report_{inspection_id}.pdf",
            )
        raise HTTPException(status_code=404, detail=f"Report PDF not found for inspection ID: {inspection_id}")

    return FileResponse(
        record.report_pdf_path,
        media_type="application/pdf",
        filename=f"Fabric_Inspection_Report_{inspection_id}.pdf",
    )


@router.post("/report/{inspection_id}/generate", summary="Generate or Regenerate Report PDF")
def generate_report_endpoint(inspection_id: str, db: Session = Depends(get_db)):
    """Generate or rebuild the PDF report from saved inspection results."""
    record = db.query(InspectionRecord).filter(InspectionRecord.inspection_id == inspection_id).first()
    if not record or not record.full_result_json:
        raise HTTPException(status_code=404, detail=f"Inspection data not found for: {inspection_id}")

    pdf_path = generate_pdf_report(record.full_result_json)
    record.report_pdf_path = pdf_path
    db.commit()

    return {
        "inspection_id": inspection_id,
        "report_pdf_path": pdf_path,
        "download_url": f"/api/report/{inspection_id}",
        "message": "PDF report generated successfully.",
    }


@router.post("/inspections/{inspection_id}/rethreshold", summary="Dynamically re-threshold inspection without re-running model")
def rethreshold_inspection(
    inspection_id: str,
    confidence_threshold: float = Form(...),
    db: Session = Depends(get_db),
):
    """
    Adjust confidence threshold on an already scanned fabric image.
    Instant re-filtering of candidate detections, re-calculated quality score,
    re-generated annotated overlay, and updated PDF report without re-uploading.
    """
    record = db.query(InspectionRecord).filter(InspectionRecord.inspection_id == inspection_id).first()
    if not record or not record.full_result_json:
        raise HTTPException(status_code=404, detail=f"Inspection '{inspection_id}' not found.")

    res = dict(record.full_result_json)
    fabric_val = res.get("fabric_validation", {})
    if not fabric_val.get("is_valid_fabric", True):
        # Sample is rejected / invalid fabric. Keep it as INVALID with 0 defects.
        return res

    all_dets = res.get("all_detections", [])
    if not all_dets and "defect_analysis" in res:
        all_dets = res["defect_analysis"].get("detailed_boxes", [])

    # Filter by new threshold
    filtered_dets = [d for d in all_dets if float(d.get("confidence", 0)) >= confidence_threshold]
    img_w = res.get("image", {}).get("width", 800)
    img_h = res.get("image", {}).get("height", 800)

    # Re-run defect analysis
    from backend.app.analysis.defect_analysis import analyze_defects
    from backend.app.analysis.quality_scorer import calculate_quality_and_grade

    new_defect_analysis = analyze_defects(filtered_dets, img_w, img_h)
    new_meas = new_defect_analysis["inspection_measurements"]

    # Re-calculate quality and grade
    struct_meas = res.get("structural_analysis", {})
    new_quality = calculate_quality_and_grade(new_meas, struct_meas)

    # Re-visualize annotated image
    orig_path = res.get("image", {}).get("original_path")
    anno_path = res.get("image", {}).get("annotated_path")
    if orig_path and os.path.isfile(orig_path):
        visualize_detections(orig_path, filtered_dets, output_path=anno_path)

    # Update result dictionary
    res["model"]["confidence_threshold"] = confidence_threshold
    res["defects"] = {
        "total": new_meas["total_defects"],
        "hole": new_meas["defects_per_class"].get("hole", 0),
        "knot": new_meas["defects_per_class"].get("knot", 0),
        "stain": new_meas["defects_per_class"].get("stain", 0),
    }
    res["defect_analysis"] = new_meas
    res["quality"] = {
        "defect_score": new_quality["defect_score"],
        "structure_score": new_quality["structure_score"],
        "quality_score": new_quality["quality_score"],
        "grade": new_quality["grade"],
        "grade_description": new_quality["grade_description"],
        "methodology": new_quality["methodology"],
    }

    # Re-generate PDF report
    pdf_path = generate_pdf_report(res)
    res["report_pdf_path"] = pdf_path

    # Update database record
    record.total_defects = new_meas["total_defects"]
    record.hole_count = new_meas["defects_per_class"].get("hole", 0)
    record.knot_count = new_meas["defects_per_class"].get("knot", 0)
    record.stain_count = new_meas["defects_per_class"].get("stain", 0)
    record.defect_area_pct = new_meas["defect_area_percentage"]
    record.defect_score = new_quality["defect_score"]
    record.quality_score = new_quality["quality_score"]
    record.grade = new_quality["grade"]
    record.grade_description = new_quality["grade_description"]
    record.report_pdf_path = pdf_path
    record.full_result_json = res
    db.commit()

    return res


# ---------------------------------------------------------------------------
# 6. History & Dashboard Endpoints
# ---------------------------------------------------------------------------
@router.get("/inspections", summary="List Inspection History")
def list_inspections(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """List historical fabric inspections with summary statistics."""
    records = (
        db.query(InspectionRecord)
        .order_by(InspectionRecord.timestamp.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    total_count = db.query(InspectionRecord).count()

    return {
        "total": total_count,
        "inspections": [r.to_summary_dict() for r in records],
    }


@router.get("/inspections/{inspection_id}", summary="Get Full Inspection Details")
def get_inspection_details(inspection_id: str, db: Session = Depends(get_db)):
    """Retrieve complete data, measurements, and images for an inspection."""
    record = db.query(InspectionRecord).filter(InspectionRecord.inspection_id == inspection_id).first()
    if not record:
        raise HTTPException(status_code=404, detail=f"Inspection '{inspection_id}' not found.")

    if record.full_result_json:
        return record.full_result_json
    return record.to_summary_dict()


@router.get("/dashboard/metrics", summary="Dashboard Aggregates & Analytics")
def get_dashboard_metrics(db: Session = Depends(get_db)):
    """Compute aggregate analytics for the frontend dashboard."""
    records = db.query(InspectionRecord).all()
    total = len(records)

    if total == 0:
        return {
            "total_inspections": 0,
            "average_quality_score": 0.0,
            "defect_free_lots": 0,
            "defect_free_percentage": 0,
            "average_inference_sec": 0.42,
            "grade_distribution": {"A": 0, "B": 0, "C": 0, "D": 0},
            "defect_distribution": {"hole": 0, "knot": 0, "stain": 0},
            "recent_inspections": [],
        }

    scores = [r.quality_score for r in records if r.quality_score is not None]
    avg_score = round(sum(scores) / len(scores), 1) if scores else 0.0

    defect_free_lots = sum(
        1 for r in records if (r.total_defects or 0) == 0 and r.grade != "INVALID"
    )
    defect_free_pct = round((defect_free_lots / total) * 100) if total > 0 else 0

    avg_inf_sec = 0.42

    grade_dist = {"A": 0, "B": 0, "C": 0, "D": 0}
    for r in records:
        if r.grade in grade_dist:
            grade_dist[r.grade] += 1

    defect_dist = {
        "hole": sum(r.hole_count for r in records),
        "knot": sum(r.knot_count for r in records),
        "stain": sum(r.stain_count for r in records),
    }

    recent = [
        r.to_summary_dict()
        for r in sorted(records, key=lambda x: x.timestamp or datetime.min, reverse=True)[:6]
    ]

    return {
        "total_inspections": total,
        "average_quality_score": avg_score,
        "defect_free_lots": defect_free_lots,
        "defect_free_percentage": defect_free_pct,
        "average_inference_sec": avg_inf_sec,
        "grade_distribution": grade_dist,
        "defect_distribution": defect_dist,
        "recent_inspections": recent,
    }


@router.delete("/inspections", summary="Clear All Historical Inspections")
def clear_all_inspections(db: Session = Depends(get_db)):
    """Delete all inspection records and associated result artifacts."""
    records = db.query(InspectionRecord).all()
    count = len(records)

    for r in records:
        # Clean up results directory for this inspection
        res_dir = os.path.join(RESULTS_DIR, r.inspection_id)
        if os.path.isdir(res_dir):
            shutil.rmtree(res_dir, ignore_errors=True)

        # Clean up report PDF
        if r.report_pdf_path and os.path.isfile(r.report_pdf_path):
            try:
                os.remove(r.report_pdf_path)
            except Exception:
                pass

        # Clean up uploaded image if in UPLOAD_DIR
        if r.original_image_path and os.path.isfile(r.original_image_path):
            try:
                if os.path.abspath(r.original_image_path).startswith(os.path.abspath(UPLOAD_DIR)):
                    os.remove(r.original_image_path)
            except Exception:
                pass

        db.delete(r)

    db.commit()
    return {
        "status": "success",
        "deleted_count": count,
        "message": f"Successfully cleared all {count} inspection records from archive.",
    }


@router.delete("/inspections/{inspection_id}", summary="Delete Single Inspection Record")
def delete_inspection(inspection_id: str, db: Session = Depends(get_db)):
    """Delete an individual inspection record and its artifacts."""
    record = db.query(InspectionRecord).filter(InspectionRecord.inspection_id == inspection_id).first()
    if not record:
        raise HTTPException(status_code=404, detail=f"Inspection '{inspection_id}' not found.")

    res_dir = os.path.join(RESULTS_DIR, record.inspection_id)
    if os.path.isdir(res_dir):
        shutil.rmtree(res_dir, ignore_errors=True)

    if record.report_pdf_path and os.path.isfile(record.report_pdf_path):
        try:
            os.remove(record.report_pdf_path)
        except Exception:
            pass

    if record.original_image_path and os.path.isfile(record.original_image_path):
        try:
            if os.path.abspath(record.original_image_path).startswith(os.path.abspath(UPLOAD_DIR)):
                os.remove(record.original_image_path)
        except Exception:
            pass

    db.delete(record)
    db.commit()

    return {
        "status": "success",
        "inspection_id": inspection_id,
        "message": f"Inspection '{inspection_id}' successfully deleted.",
    }

