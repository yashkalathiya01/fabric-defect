"""
Fabric AI Inspection System - Master Inspection Coordinator
============================================================

Fuses AI defect detection, OpenCV structural analysis, visualization,
and quality scoring into the unified final inspection result.
Includes pre-inspection domain validation to suppress defect false-alarms
on non-fabric images (animals, birds, vehicles, food, screenshots).
"""

import os
import shutil
import uuid
import time
from datetime import datetime
from typing import Any
import cv2

from backend.app.config import RESULTS_DIR, CONFIDENCE_THRESHOLD
from backend.app.model.detector import detect_defects
from backend.app.analysis.visualizer import visualize_detections
from backend.app.analysis.defect_analysis import analyze_defects
from backend.app.analysis.structure_analyzer import analyze_fabric_structure
from backend.app.analysis.quality_scorer import calculate_quality_and_grade
from backend.app.analysis.fabric_validator import validate_fabric_image


def run_full_inspection(
    image_path: str,
    confidence_threshold: float | None = None,
    inspection_id: str | None = None,
) -> dict[str, Any]:
    """
    Run end-to-end inspection:
      0. Fabric Domain Validation (checks if image is authentic physical textile)
      1. AI Defect Detection (Faster R-CNN) - bypassed if image is non-fabric
      2. Detection Visualization & Bounding Boxes
      3. Defect Statistical Analysis
      4. OpenCV Structural & Warp/Weft Analysis
      5. Quality Scoring & Fabric Grading

    Returns:
        Complete inspection result matching Stage 9 specifications.
    """
    if not os.path.isfile(image_path):
        raise FileNotFoundError(f"Input image not found: {image_path}")

    start_time = time.time()
    iid = inspection_id or f"INSP-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
    timestamp_iso = datetime.now().isoformat()

    # 0. Fabric Domain Validation
    fabric_val = validate_fabric_image(image_path)
    is_valid_fabric = fabric_val.get("is_valid_fabric", True)

    insp_results_dir = os.path.join(RESULTS_DIR, iid)
    os.makedirs(insp_results_dir, exist_ok=True)
    annotated_img_path = os.path.join(insp_results_dir, "annotated_detection.jpg")

    conf_thresh = confidence_threshold if confidence_threshold is not None else CONFIDENCE_THRESHOLD

    # If image is NOT a valid fabric (e.g. parrot, dog, car, screenshot, blank surface):
    # SUPPRESS Faster R-CNN defect proposal completely to avoid hallucinated false defects.
    if not is_valid_fabric:
        # Read dimensions without running detector
        tmp_img = cv2.imread(image_path)
        if tmp_img is not None:
            img_h, img_w = tmp_img.shape[:2]
        else:
            img_w, img_h = 640, 640

        # Save clean copy of original image without any defect boxes
        shutil.copyfile(image_path, annotated_img_path)

        detections = []
        all_detections = []
        insp_measurements = {
            "total_defects": 0,
            "defects_per_class": {"hole": 0, "knot": 0, "stain": 0},
            "defect_area_percentage": 0.0,
            "defect_density_per_sq_meter": 0.0,
            "detailed_boxes": [],
        }
        struct_meas = {
            "warp_angle": None,
            "weft_angle": None,
            "warp_spacing_px": None,
            "weft_spacing_px": None,
            "warp_spacing_std": None,
            "weft_spacing_std": None,
            "alignment_deviation_deg": None,
            "orientation_confidence": 0.0,
        }
        structure_res = {"measurements": struct_meas, "visualization_paths": {}}
        quality_res = {
            "grade": "INVALID",
            "quality_score": 0.0,
            "defect_score": 0.0,
            "structure_score": 0.0,
            "grade_description": f"Sample Rejected: {fabric_val['message']}",
            "methodology": {
                "formula": "Domain Validation Failed - Defect Scanning Suppressed",
                "defect_weight": 0.0,
                "structure_weight": 0.0,
                "deductions": {"non_fabric_rejection": 100.0},
            },
        }
        inference_time_ms = 0.0

    else:
        # 1. AI Defect Detection (Faster R-CNN)
        detection_res = detect_defects(image_path, confidence_threshold=conf_thresh)
        detections = detection_res["detections"]
        all_detections = detection_res.get("all_detections", detections)
        img_w = detection_res["image_width"]
        img_h = detection_res["image_height"]
        inference_time_ms = detection_res["inference_time_ms"]

        # 2. Visualization
        visualize_detections(image_path, detections, output_path=annotated_img_path)

        # 3. Defect Statistical Analysis
        defect_analysis_res = analyze_defects(detections, img_w, img_h)
        insp_measurements = defect_analysis_res["inspection_measurements"]

        # 4. OpenCV Structural & Warp/Weft Analysis
        struct_results_dir = os.path.join(insp_results_dir, "structural")
        structure_res = analyze_fabric_structure(image_path, output_dir=struct_results_dir)
        struct_meas = structure_res.get("measurements", {})

        # 5. Quality Score & Grading
        quality_res = calculate_quality_and_grade(insp_measurements, struct_meas)

    total_time_ms = round((time.time() - start_time) * 1000.0, 1)

    # 6. Build Standardized Inspection Result
    result = {
        "inspection_id": iid,
        "timestamp": timestamp_iso,
        "is_valid_fabric": is_valid_fabric,
        "material_status": "Fabric Verified" if is_valid_fabric else "Non-Fabric",
        "detection_status": "Defects Detected" if (is_valid_fabric and len(detections) > 0) else ("No Defects" if is_valid_fabric else "Rejected"),
        "message": (
            f"Fabric verified — {len(detections)} defect(s) detected."
            if (is_valid_fabric and len(detections) > 0)
            else (
                "Fabric verified — no defects detected."
                if is_valid_fabric
                else fabric_val.get(
                    "message",
                    "The uploaded specimen was identified as invalid photo rather than an authentic textile fabric photo. Automated Faster R-CNN defect proposal was bypassed to prevent false-positive defect alarms on non-fabric surfaces."
                )
            )
        ),
        "fabric_validation": fabric_val,
        "image": {
            "original_path": image_path,
            "annotated_path": annotated_img_path,
            "width": img_w,
            "height": img_h,
        },
        "model": {
            "name": "Faster R-CNN + ResNet-50 FPN",
            "classes": ["hole", "knot", "stain"],
            "device": "cpu",
            "confidence_threshold": conf_thresh,
        },
        "defects": {
            "total": insp_measurements["total_defects"],
            "hole": insp_measurements["defects_per_class"].get("hole", 0),
            "knot": insp_measurements["defects_per_class"].get("knot", 0),
            "stain": insp_measurements["defects_per_class"].get("stain", 0),
        },
        "all_detections": all_detections,
        "defect_analysis": insp_measurements,
        "structural_analysis": {
            "warp_angle": struct_meas.get("warp_angle"),
            "weft_angle": struct_meas.get("weft_angle"),
            "warp_spacing": struct_meas.get("warp_spacing_px"),
            "weft_spacing": struct_meas.get("weft_spacing_px"),
            "warp_spacing_std": struct_meas.get("warp_spacing_std"),
            "weft_spacing_std": struct_meas.get("weft_spacing_std"),
            "alignment_deviation": struct_meas.get("alignment_deviation_deg"),
            "orientation_confidence": struct_meas.get("orientation_confidence", 0.0),
            "visualization_paths": structure_res.get("visualization_paths", {}),
        },
        "quality": {
            "defect_score": quality_res["defect_score"],
            "structure_score": quality_res["structure_score"],
            "quality_score": quality_res["quality_score"],
            "grade": quality_res["grade"],
            "grade_description": quality_res["grade_description"],
            "methodology": quality_res["methodology"],
        },
        "timing": {
            "inference_time_ms": inference_time_ms,
            "total_inspection_time_ms": total_time_ms,
        },
    }

    return result
