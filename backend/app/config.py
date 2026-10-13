"""
Fabric AI Inspection System - Configuration
=============================================

Centralised configuration for the application.
The model path can be overridden by the FABRIC_MODEL_PATH environment variable.

Priority:
    1. FABRIC_MODEL_PATH environment variable
    2. Default local Windows path (below)
"""

import os


# ---------------------------------------------------------------------------
# Model path
# ---------------------------------------------------------------------------
# Default: the trained Faster R-CNN checkpoint on this Windows machine.
# On another machine, set the FABRIC_MODEL_PATH environment variable.
_DEFAULT_MODEL_PATH = r"E:\Project\models\object detection\best_model.pth"

MODEL_PATH: str = os.environ.get("FABRIC_MODEL_PATH", _DEFAULT_MODEL_PATH)


# ---------------------------------------------------------------------------
# Model architecture (must match the checkpoint)
# ---------------------------------------------------------------------------
# These values were extracted from the training pipeline:
#   fabric_frcnn_kaggle (3).ipynb
#
# Architecture: Faster R-CNN + ResNet-50 FPN (torchvision)
# num_classes = 4  (0=background, 1=hole, 2=knot, 3=stain)
# trainable_backbone_layers = 5
# Anchors: torchvision defaults
NUM_CLASSES: int = 4  # background + 3 defect classes

CLASS_NAMES: dict[int, str] = {
    1: "hole",
    2: "knot",
    3: "stain",
}

CLASS_COLORS: dict[int, tuple[int, int, int]] = {
    1: (255, 80, 80),    # hole  → red
    2: (80, 200, 255),   # knot  → cyan
    3: (170, 120, 255),  # stain → purple
}


# ---------------------------------------------------------------------------
# Inference
# ---------------------------------------------------------------------------
CONFIDENCE_THRESHOLD: float = float(
    os.environ.get("FABRIC_CONFIDENCE_THRESHOLD", "0.50")
)

# The minimum score the model's internal NMS will keep.
# This should be low; the real threshold is CONFIDENCE_THRESHOLD above.
BOX_SCORE_THRESH_INFER: float = 0.01
BOX_DETECTIONS_PER_IMG: int = 100

# Input image dimensions used during training.
# The model's built-in transform will resize to min_size/max_size.
MIN_SIZE: int = 800
MAX_SIZE: int = 1333


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
UPLOAD_DIR: str = os.environ.get(
    "FABRIC_UPLOAD_DIR",
    os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads"),
)
RESULTS_DIR: str = os.environ.get(
    "FABRIC_RESULTS_DIR",
    os.path.join(os.path.dirname(os.path.dirname(__file__)), "results"),
)


# ---------------------------------------------------------------------------
# Quality scoring (prototype weights — not an industry standard)
# ---------------------------------------------------------------------------
QUALITY_WEIGHTS = {
    "defect_weight": 0.60,
    "structure_weight": 0.40,
}

GRADE_THRESHOLDS = {
    "A": 90,
    "B": 75,
    "C": 60,
    "D": 0,   # anything below 60
}


# ---------------------------------------------------------------------------
# Security
# ---------------------------------------------------------------------------
ALLOWED_EXTENSIONS: set[str] = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp"}
MAX_FILE_SIZE_MB: int = 50
MAX_IMAGE_DIMENSION: int = 8192
