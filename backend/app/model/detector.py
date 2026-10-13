"""
Fabric AI Inspection System - Defect Detector
===============================================

Runs inference on a single fabric image using the loaded Faster R-CNN model.

Usage:
    from backend.app.model.detector import detect_defects
    result = detect_defects("path/to/fabric.jpg")
"""

import os
import time
import logging
from typing import Any

import numpy as np
import torch
from PIL import Image

from backend.app.config import (
    CONFIDENCE_THRESHOLD,
    CLASS_NAMES,
    ALLOWED_EXTENSIONS,
    MAX_IMAGE_DIMENSION,
)
from backend.app.model.model_loader import load_model

logger = logging.getLogger(__name__)


def _load_image(image_path: str) -> tuple[torch.Tensor, np.ndarray, int, int]:
    """
    Load an image from disk and convert to a CHW float32 tensor in [0, 1].

    Returns:
        (tensor, numpy_rgb, width, height)
    """
    if not os.path.isfile(image_path):
        raise FileNotFoundError(f"Image not found: {image_path}")

    ext = os.path.splitext(image_path)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(
            f"Unsupported image format '{ext}'. "
            f"Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        )

    try:
        pil_img = Image.open(image_path).convert("RGB")
    except Exception as e:
        raise ValueError(f"Cannot open image '{image_path}': {e}") from e

    w, h = pil_img.size
    if w > MAX_IMAGE_DIMENSION or h > MAX_IMAGE_DIMENSION:
        raise ValueError(
            f"Image dimensions ({w}x{h}) exceed maximum ({MAX_IMAGE_DIMENSION}x{MAX_IMAGE_DIMENSION})."
        )

    img_np = np.array(pil_img, dtype=np.uint8)  # HWC, RGB, 0-255
    tensor = torch.from_numpy(img_np).permute(2, 0, 1).float() / 255.0  # CHW, 0-1

    return tensor, img_np, w, h


def detect_defects(
    image_path: str,
    confidence_threshold: float | None = None,
) -> dict[str, Any]:
    """
    Run defect detection on a single fabric image.

    Args:
        image_path: Path to the input image file.
        confidence_threshold: Minimum confidence to include a detection.
                              Defaults to config.CONFIDENCE_THRESHOLD.

    Returns:
        {
            "image_path": str,
            "image_width": int,
            "image_height": int,
            "inference_time_ms": float,
            "device": str,
            "confidence_threshold": float,
            "model": {
                "name": "Faster R-CNN + ResNet-50 FPN",
                "classes": ["hole", "knot", "stain"],
            },
            "detections": [
                {
                    "class": "hole",
                    "label": 1,
                    "confidence": 0.91,
                    "bbox": [x1, y1, x2, y2],
                },
                ...
            ],
            "summary": {
                "total": int,
                "hole": int,
                "knot": int,
                "stain": int,
            },
        }
    """
    threshold = confidence_threshold if confidence_threshold is not None else CONFIDENCE_THRESHOLD

    # Load model (singleton — no repeated 500 MB loads)
    model, class_names, device = load_model()

    # Load image
    tensor, img_np, w, h = _load_image(image_path)
    tensor = tensor.to(device)

    # Run inference
    logger.info("Running inference on '%s' (%dx%d)...", os.path.basename(image_path), w, h)
    t0 = time.time()

    with torch.inference_mode():
        outputs = model([tensor])

    inference_ms = (time.time() - t0) * 1000.0
    logger.info("Inference completed in %.1f ms", inference_ms)

    # Extract predictions
    out = outputs[0]
    boxes = out["boxes"].cpu().numpy()       # (N, 4) — x1, y1, x2, y2
    scores = out["scores"].cpu().numpy()     # (N,)
    labels = out["labels"].cpu().numpy()     # (N,)

    # Build all detections (down to 0.05 confidence for live frontend re-thresholding)
    all_detections = []
    for box, score, label in zip(boxes, scores, labels):
        if float(score) >= 0.05:
            label_int = int(label)
            all_detections.append({
                "class": class_names.get(label_int, f"unknown_{label_int}"),
                "label": label_int,
                "confidence": round(float(score), 4),
                "bbox": [round(float(c), 2) for c in box],
            })

    # Filter by confidence threshold
    keep = scores >= threshold
    filtered_boxes = boxes[keep]
    filtered_scores = scores[keep]
    filtered_labels = labels[keep]

    # Build filtered detection list
    detections = []
    for box, score, label in zip(filtered_boxes, filtered_scores, filtered_labels):
        label_int = int(label)
        detections.append({
            "class": class_names.get(label_int, f"unknown_{label_int}"),
            "label": label_int,
            "confidence": round(float(score), 4),
            "bbox": [round(float(c), 2) for c in box],
        })

    # Summary counts
    summary = {"total": len(detections)}
    for name in class_names.values():
        summary[name] = sum(1 for d in detections if d["class"] == name)

    return {
        "image_path": image_path,
        "image_width": w,
        "image_height": h,
        "inference_time_ms": round(inference_ms, 2),
        "device": str(device),
        "confidence_threshold": threshold,
        "model": {
            "name": "Faster R-CNN + ResNet-50 FPN",
            "classes": list(class_names.values()),
        },
        "detections": detections,
        "all_detections": all_detections,
        "summary": summary,
    }
