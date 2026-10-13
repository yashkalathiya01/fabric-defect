# REST API Documentation

## Fabric AI Inspection System API Specification

The backend exposes a comprehensive RESTful API built with FastAPI, providing access to defect detection, OpenCV structural weave analysis, quality scoring, database archives, and automated PDF reports.

- **Base URL**: `http://127.0.0.1:8000`
- **Interactive OpenAPI Documentation**: `http://127.0.0.1:8000/docs`
- **ReDoc Documentation**: `http://127.0.0.1:8000/redoc`

---

## 1. System Health

### `GET /health` or `GET /api/health`
Check the operational status of the inspection backend, model preloading, and active device.

#### Response (200 OK)
```json
{
  "status": "healthy",
  "timestamp": "2026-09-21T20:44:18.746509",
  "model": {
    "name": "Faster R-CNN + ResNet-50 FPN",
    "classes": {
      "1": "hole",
      "2": "knot",
      "3": "stain"
    },
    "num_classes": 4,
    "loaded": true,
    "device": "cpu",
    "model_path": "E:\\Project\\models\\object detection\\best_model.pth"
  },
  "version": "1.0.0"
}
```

---

## 2. AI Defect Detection

### `POST /predict` or `POST /api/predict`
Executes Faster R-CNN object detection on a fabric sample. Generates bounding boxes, class labels, confidence scores, and an annotated visualization image.

#### Request (multipart/form-data)
| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `file` | Binary (File) | Yes | -- | Fabric image file (JPG, PNG, WEBP) |
| `confidence_threshold` | Float | No | 0.50 | Minimum confidence threshold for detected defects |

#### Response (200 OK)
```json
{
  "image_path": "E:\\Project\\backend\\uploads\\fabric_20260921_120000_abc123.jpg",
  "image_width": 640,
  "image_height": 640,
  "inference_time_ms": 4118.6,
  "device": "cpu",
  "confidence_threshold": 0.5,
  "model": {
    "name": "Faster R-CNN + ResNet-50 FPN",
    "classes": ["hole", "knot", "stain"]
  },
  "detections": [
    {
      "class": "hole",
      "label": 1,
      "confidence": 0.9973,
      "bbox": [102.3, 220.4, 255.4, 395.7]
    }
  ],
  "summary": {
    "total": 1,
    "hole": 1,
    "knot": 0,
    "stain": 0
  },
  "annotated_image_url": "/static/results/fabric_annotated.jpg",
  "original_image_url": "/static/uploads/fabric.jpg"
}
```

---

## 3. OpenCV Structural Analysis

### `POST /analyze` or `POST /api/analyze`
Runs the OpenCV textile analysis pipeline on a fabric sample. Extracts thread orientation angles, spacing regularity, and intermediate debug stages.

#### Request (multipart/form-data)
| Parameter | Type | Required | Description |
|---|---|---|---|
| `file` | Binary (File) | Yes | Fabric image file |

#### Response (200 OK)
```json
{
  "status": "success",
  "measurements": {
    "dominant_directions": {
      "warp_direction_deg": 135.0,
      "weft_direction_deg": 178.74
    },
    "warp_angle": 135.0,
    "weft_angle": 178.74,
    "warp_spacing_px": 28.5,
    "weft_spacing_px": 24.2,
    "warp_spacing_std": 3.1,
    "weft_spacing_std": 2.8,
    "alignment_deviation_deg": 46.26,
    "orientation_confidence": 0.85,
    "line_statistics": {
      "total_lines_detected": 142,
      "warp_line_count": 86,
      "weft_line_count": 56
    }
  },
  "visualization_urls": {
    "grayscale": "/static/results/structural/fabric_gray.jpg",
    "threshold": "/static/results/structural/fabric_thresh.jpg",
    "canny_edges": "/static/results/structural/fabric_canny.jpg",
    "hough_lines": "/static/results/structural/fabric_hough.jpg",
    "warp_lines": "/static/results/structural/fabric_warp.jpg",
    "weft_lines": "/static/results/structural/fabric_weft.jpg"
  }
}
```

---

## 4. Master Full Inspection

### `POST /inspect` or `POST /api/inspect`
Executes the unified inspection workflow (AI Defect Detection + OpenCV Structural Analysis + Quality Scoring + Grading + Database Storage + Automatic PDF Generation).

#### Request (multipart/form-data)
| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `file` | Binary (File) | Yes | -- | Fabric image file |
| `confidence_threshold` | Float | No | 0.50 | Detection confidence threshold |

#### Response (200 OK)
```json
{
  "inspection_id": "INSP-20260921-42AB65",
  "timestamp": "2026-09-21T20:41:45.123456",
  "image": {
    "original_path": "...",
    "annotated_path": "...",
    "width": 640,
    "height": 640,
    "original_url": "/static/uploads/fabric.jpg",
    "annotated_url": "/static/results/INSP-20260921-42AB65/annotated_detection.jpg"
  },
  "model": {
    "name": "Faster R-CNN + ResNet-50 FPN",
    "classes": ["hole", "knot", "stain"],
    "device": "cpu",
    "confidence_threshold": 0.5
  },
  "defects": {
    "total": 1,
    "hole": 1,
    "knot": 0,
    "stain": 0
  },
  "defect_analysis": {
    "total_defects": 1,
    "defects_per_class": { "hole": 1 },
    "defect_area_px": 26824.5,
    "defect_area_percentage": 6.55,
    "defect_density_per_megapixel": 2.44,
    "detailed_boxes": [...]
  },
  "structural_analysis": {
    "warp_angle": 135.0,
    "weft_angle": 178.74,
    "alignment_deviation": 46.26,
    "orientation_confidence": 0.85,
    "visualization_urls": { ... }
  },
  "quality": {
    "defect_score": 35.0,
    "structure_score": 38.0,
    "quality_score": 36.2,
    "grade": "D",
    "grade_description": "Reject / Defective (Failed Quality Inspection)",
    "methodology": {
      "defect_weight": 0.6,
      "structure_weight": 0.4,
      "formula": "quality_score = (0.6 * defect_score) + (0.4 * structure_score)",
      "grading_thresholds": "Prototype grading thresholds (A: 90-100, B: 75-89, C: 60-74, D: <60)",
      "disclaimer": "Engineering prototype formula. Not a certified ASTM/ISO standard."
    }
  },
  "timing": {
    "inference_time_ms": 4118.6,
    "total_inspection_time_ms": 4560.2
  },
  "report_download_url": "/api/report/INSP-20260921-42AB65"
}
```

---

## 5. PDF Inspection Reports

### `GET /report/{inspection_id}` or `GET /api/report/{inspection_id}`
Download the official generated PDF report for an inspection.
- **Response**: File stream (`application/pdf`) with filename `Fabric_Inspection_Report_{inspection_id}.pdf`.

### `POST /report/{inspection_id}/generate` or `POST /api/report/{inspection_id}/generate`
Regenerate a PDF report from database records.

---

## 6. History & Dashboard Analytics

### `GET /api/inspections`
Paginated list of historical inspection records.
- Query parameters: `skip` (default 0), `limit` (default 50, max 200)

### `GET /api/inspections/{inspection_id}`
Retrieve complete inspection data, measurements, and images for an inspection.

### `GET /api/dashboard/metrics`
Retrieve aggregate metrics for the dashboard (total inspections, defect breakdown, grade distribution, recent scans).

### `GET /api/samples`
Returns a curated list of benchmark fabric sample images available for 1-click testing.
