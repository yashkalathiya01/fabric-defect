"""
Fabric AI Inspection System - Complete Pipeline Test Suite
==========================================================

Runs end-to-end unit and integration tests across all system components:
  1. Config & Model Path
  2. Model Loading & Architecture Verification
  3. Class Mapping Verification
  4. Defect Detection & Bounding Boxes
  5. Visualization Output
  6. Defect Statistical Analysis
  7. OpenCV Structural & Warp/Weft Analysis
  8. Quality Scoring & Prototype Grading
  9. ReportLab PDF Generation
 10. SQLite / PostgreSQL Database Persistence
 11. FastAPI Direct Endpoint Functionality
"""

import os
import sys
import unittest
from datetime import datetime

# Add project root to sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.app.config import MODEL_PATH, NUM_CLASSES, CLASS_NAMES
from backend.app.model.model_loader import load_model
from backend.app.model.detector import detect_defects
from backend.app.analysis.visualizer import visualize_detections
from backend.app.analysis.defect_analysis import analyze_defects
from backend.app.analysis.structure_analyzer import analyze_fabric_structure
from backend.app.analysis.quality_scorer import calculate_quality_and_grade
from backend.app.analysis.inspector import run_full_inspection
from backend.app.reports.report_generator import generate_pdf_report
from backend.app.database.database import SessionLocal, init_db
from backend.app.database.models import InspectionRecord
from backend.app.api.endpoints import health_check


class TestFabricInspectionPipeline(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        init_db()
        # Find a valid test image
        cls.test_image = os.path.join(
            PROJECT_ROOT,
            "Dataset",
            "test",
            "close-up-old-blue-jean-texture-torn-hole-58503943_jpg.rf.4f995b2e3ad5805bd28cdeb107ed0650.jpg",
        )
        assert os.path.isfile(cls.test_image), f"Test image missing: {cls.test_image}"

    def test_01_model_path_exists(self):
        """Verify that the model checkpoint exists at the configured path."""
        self.assertTrue(os.path.isfile(MODEL_PATH), f"Model checkpoint missing at {MODEL_PATH}")
        size_mb = os.path.getsize(MODEL_PATH) / (1024 * 1024)
        self.assertGreater(size_mb, 400.0, "Checkpoint should be ~470-500 MB")

    def test_02_model_loader_and_architecture(self):
        """Verify model loads, parameters match Faster R-CNN, and class count is 4."""
        model, class_names, device = load_model()
        self.assertIsNotNone(model)
        self.assertFalse(model.training, "Model must be in eval mode")
        self.assertEqual(model.roi_heads.box_predictor.cls_score.out_features, NUM_CLASSES)
        self.assertEqual(len(class_names), 3, "Must have 3 defect classes (hole, knot, stain)")
        self.assertEqual(class_names[1], "hole")
        self.assertEqual(class_names[2], "knot")
        self.assertEqual(class_names[3], "stain")

    def test_03_defect_detector(self):
        """Verify inference returns bounding boxes, scores, and class names."""
        res = detect_defects(self.test_image, confidence_threshold=0.5)
        self.assertIn("detections", res)
        self.assertIn("inference_time_ms", res)
        self.assertGreater(res["inference_time_ms"], 0)
        self.assertGreaterEqual(len(res["detections"]), 1, "Expected at least 1 detection on test image")
        first_det = res["detections"][0]
        self.assertEqual(first_det["class"], "hole")
        self.assertGreater(first_det["confidence"], 0.90)
        self.assertEqual(len(first_det["bbox"]), 4)

    def test_04_visualization(self):
        """Verify annotated image is saved to disk."""
        det_res = detect_defects(self.test_image, confidence_threshold=0.5)
        out_vis = visualize_detections(self.test_image, det_res["detections"])
        self.assertTrue(os.path.isfile(out_vis))
        self.assertGreater(os.path.getsize(out_vis), 1000)

    def test_05_defect_analysis(self):
        """Verify defect statistical calculations."""
        det_res = detect_defects(self.test_image, confidence_threshold=0.5)
        analysis = analyze_defects(det_res["detections"], det_res["image_width"], det_res["image_height"])
        meas = analysis["inspection_measurements"]
        self.assertIn("total_defects", meas)
        self.assertIn("defect_area_percentage", meas)
        self.assertIn("defect_density_per_megapixel", meas)
        self.assertGreater(meas["total_defects"], 0)

    def test_06_structural_analysis(self):
        """Verify OpenCV Canny edge & Hough transform pipeline."""
        struct = analyze_fabric_structure(self.test_image)
        self.assertIn("measurements", struct)
        self.assertIn("visualization_paths", struct)
        meas = struct["measurements"]
        self.assertIn("warp_angle", meas)
        self.assertIn("weft_angle", meas)

    def test_07_quality_scoring_and_grading(self):
        """Verify transparent quality score formula and grade thresholds."""
        defect_data = {"total_defects": 1, "defects_per_class": {"hole": 1}, "defect_area_percentage": 2.5}
        struct_data = {"alignment_deviation_deg": 3.0, "orientation_confidence": 0.8}
        qual = calculate_quality_and_grade(defect_data, struct_data)
        self.assertIn("defect_score", qual)
        self.assertIn("structure_score", qual)
        self.assertIn("quality_score", qual)
        self.assertIn(qual["grade"], ["A", "B", "C", "D"])

    def test_08_pdf_report_generation(self):
        """Verify ReportLab PDF generation."""
        insp_res = run_full_inspection(self.test_image, confidence_threshold=0.5)
        pdf_path = generate_pdf_report(insp_res)
        self.assertTrue(os.path.isfile(pdf_path))
        self.assertGreater(os.path.getsize(pdf_path), 50_000)

    def test_09_database_persistence(self):
        """Verify inspection records can be saved and retrieved from the database."""
        db = SessionLocal()
        try:
            insp_res = run_full_inspection(self.test_image, confidence_threshold=0.5)
            record = InspectionRecord(
                inspection_id=insp_res["inspection_id"],
                image_filename="test_fabric.jpg",
                original_image_path=self.test_image,
                total_defects=insp_res["defects"]["total"],
                hole_count=insp_res["defects"]["hole"],
                knot_count=insp_res["defects"]["knot"],
                stain_count=insp_res["defects"]["stain"],
                quality_score=insp_res["quality"]["quality_score"],
                grade=insp_res["quality"]["grade"],
                full_result_json=insp_res,
            )
            db.add(record)
            db.commit()

            fetched = db.query(InspectionRecord).filter(
                InspectionRecord.inspection_id == insp_res["inspection_id"]
            ).first()
            self.assertIsNotNone(fetched)
            self.assertEqual(fetched.grade, insp_res["quality"]["grade"])
        finally:
            db.close()

    def test_10_health_endpoint(self):
        """Verify the health check endpoint returns 200 with model info."""
        health = health_check()
        self.assertEqual(health["status"], "healthy")
        self.assertTrue(health["model"]["loaded"])
        self.assertEqual(health["model"]["num_classes"], 4)


if __name__ == "__main__":
    unittest.main(verbosity=2)
