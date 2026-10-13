"""
Fabric AI Inspection System - Defect Analysis
==============================================

Calculates quantitative inspection measurements from defect detections:
- Total defects and per-class distribution
- Defect density (defects per 100,000 pixels & per megapixel)
- Bounding box areas and defect area percentage (% of fabric affected)
- Largest defect and average defect dimensions
- Confidence statistics (min, max, mean, std)

NOTE:
Inspection measurements are strictly separated from Model Evaluation Metrics.
Defect detection results are NEVER labeled as "accuracy".
"""

import math
from typing import Any
import numpy as np


def analyze_defects(
    detections: list[dict[str, Any]],
    image_width: int,
    image_height: int,
) -> dict[str, Any]:
    """
    Perform deep statistical analysis on detected fabric defects.

    Args:
        detections: List of detection objects (class, confidence, bbox=[x1, y1, x2, y2]).
        image_width: Total image width in pixels.
        image_height: Total image height in pixels.

    Returns:
        Structured inspection measurement dictionary.
    """
    total_area_px = max(1, image_width * image_height)
    total_defects = len(detections)

    # Defect class counts
    class_counts: dict[str, int] = {}
    class_areas: dict[str, float] = {}
    boxes_data = []
    confidences = []

    for d in detections:
        cls = d.get("class", "unknown")
        conf = float(d.get("confidence", 0.0))
        bbox = d.get("bbox", [0, 0, 0, 0])

        x1, y1, x2, y2 = [float(c) for c in bbox]
        w = max(0.0, x2 - x1)
        h = max(0.0, y2 - y1)
        area = w * h

        class_counts[cls] = class_counts.get(cls, 0) + 1
        class_areas[cls] = class_areas.get(cls, 0.0) + area

        confidences.append(conf)
        boxes_data.append({
            "class": cls,
            "confidence": conf,
            "bbox": [round(x1, 1), round(y1, 1), round(x2, 1), round(y2, 1)],
            "width": round(w, 1),
            "height": round(h, 1),
            "area_px": round(area, 1),
            "aspect_ratio": round(w / max(h, 1e-4), 2),
        })

    # Areas & sizes
    areas = [b["area_px"] for b in boxes_data]
    total_defect_area_px = sum(areas)
    defect_area_pct = round((total_defect_area_px / total_area_px) * 100.0, 4)

    # Largest & average defect
    if boxes_data:
        largest_defect = max(boxes_data, key=lambda b: b["area_px"])
        avg_defect_area = round(float(np.mean(areas)), 1)
        avg_defect_width = round(float(np.mean([b["width"] for b in boxes_data])), 1)
        avg_defect_height = round(float(np.mean([b["height"] for b in boxes_data])), 1)
    else:
        largest_defect = None
        avg_defect_area = 0.0
        avg_defect_width = 0.0
        avg_defect_height = 0.0

    # Defect density calculations
    # 1. Defects per 100k pixels
    density_per_100k_px = round((total_defects / (total_area_px / 100_000.0)), 3)
    # 2. Defects per Megapixel
    density_per_mp = round((total_defects / (total_area_px / 1_000_000.0)), 3)

    # Confidence statistics
    if confidences:
        conf_stats = {
            "min": round(float(np.min(confidences)), 4),
            "max": round(float(np.max(confidences)), 4),
            "mean": round(float(np.mean(confidences)), 4),
            "std": round(float(np.std(confidences)), 4),
        }
    else:
        conf_stats = {
            "min": 0.0,
            "max": 0.0,
            "mean": 0.0,
            "std": 0.0,
        }

    # Defect severity categorization
    severity_distribution = {"minor": 0, "moderate": 0, "critical": 0}
    for b in boxes_data:
        # Criteria: hole is inherently more severe than knot or surface stain
        cls = b["class"]
        area_ratio = b["area_px"] / total_area_px
        if cls == "hole" or area_ratio > 0.02:
            severity_distribution["critical"] += 1
        elif cls == "knot" or area_ratio > 0.005:
            severity_distribution["moderate"] += 1
        else:
            severity_distribution["minor"] += 1

    return {
        "inspection_measurements": {
            "total_defects": total_defects,
            "defects_per_class": class_counts,
            "defect_area_px": round(total_defect_area_px, 1),
            "defect_area_percentage": defect_area_pct,
            "defect_density_per_100k_px": density_per_100k_px,
            "defect_density_per_megapixel": density_per_mp,
            "average_defect_size": {
                "area_px": avg_defect_area,
                "width_px": avg_defect_width,
                "height_px": avg_defect_height,
            },
            "largest_defect": largest_defect,
            "severity_distribution": severity_distribution,
            "confidence_statistics": conf_stats,
            "detailed_boxes": boxes_data,
        },
        "model_evaluation_reference": {
            "architecture": "Faster R-CNN + ResNet-50 FPN",
            "benchmark_dataset": "Fabric Defect Dataset (Roboflow)",
            "validation_mAP50": 0.8344,
            "validation_F1": 0.7589,
            "note": "Benchmark metrics are from model validation. Runtime inspection does not compute ground-truth accuracy.",
        },
    }
