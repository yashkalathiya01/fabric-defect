"""
Fabric AI Inspection System - Model Loader
============================================

Loads the trained Faster R-CNN + ResNet-50 FPN model from a local checkpoint.

The checkpoint format (as saved by the training pipeline):
    {
        "model":      model.state_dict(),
        "config":     { "num_classes": 4, ... },
        "class_names": { 1: "hole", 2: "knot", 3: "stain" },
        "epoch":      int,
        "best":       { "map50": float, ... },
        ...
    }

Usage:
    from backend.app.model.model_loader import load_model
    model, class_names, device = load_model()
"""

import os
import sys
import time
import logging

import torch
import torchvision
from torchvision.models.detection.faster_rcnn import FastRCNNPredictor

from backend.app.config import (
    MODEL_PATH,
    NUM_CLASSES,
    CLASS_NAMES,
    MIN_SIZE,
    MAX_SIZE,
    BOX_SCORE_THRESH_INFER,
    BOX_DETECTIONS_PER_IMG,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Module-level singleton: the model is loaded ONCE
# ---------------------------------------------------------------------------
_model = None
_class_names = None
_device = None


def _build_architecture(num_classes: int, device: torch.device) -> torch.nn.Module:
    """
    Reconstruct the exact Faster R-CNN architecture expected by the checkpoint.

    Architecture details (from training notebook):
      - torchvision.models.detection.fasterrcnn_resnet50_fpn
      - Replace the classifier head with FastRCNNPredictor(in_features, num_classes)
      - Default anchor sizes and aspect ratios
      - trainable_backbone_layers = 5
    """
    model = torchvision.models.detection.fasterrcnn_resnet50_fpn(
        weights=None,              # we load our own weights
        weights_backbone=None,     # no need for ImageNet backbone
        min_size=MIN_SIZE,
        max_size=MAX_SIZE,
        box_detections_per_img=BOX_DETECTIONS_PER_IMG,
        box_score_thresh=BOX_SCORE_THRESH_INFER,
        trainable_backbone_layers=5,
    )

    # Replace the classification head to match num_classes
    in_features = model.roi_heads.box_predictor.cls_score.in_features
    model.roi_heads.box_predictor = FastRCNNPredictor(in_features, num_classes)

    # Verify the head width
    assert model.roi_heads.box_predictor.cls_score.out_features == num_classes, (
        f"Head has {model.roi_heads.box_predictor.cls_score.out_features} outputs "
        f"but num_classes={num_classes} was expected."
    )

    return model.to(device)


def _detect_device() -> torch.device:
    """Select CUDA if available, otherwise CPU."""
    if torch.cuda.is_available():
        device = torch.device("cuda")
        props = torch.cuda.get_device_properties(0)
        logger.info(
            "CUDA device: %s | %.2f GB | SM %d.%d",
            props.name,
            props.total_mem / 1024**3 if hasattr(props, "total_mem") else props.total_memory / 1024**3,
            props.major,
            props.minor,
        )
    else:
        device = torch.device("cpu")
        logger.info("CUDA not available — using CPU (inference will be slower)")
    return device


def load_model(
    model_path: str | None = None,
    force_reload: bool = False,
) -> tuple[torch.nn.Module, dict[int, str], torch.device]:
    """
    Load the Faster R-CNN model from the checkpoint.

    Returns:
        (model, class_names, device)

    The model is loaded only ONCE and cached in module-level globals.
    Subsequent calls return the cached instance unless force_reload=True.
    """
    global _model, _class_names, _device

    if _model is not None and not force_reload:
        return _model, _class_names, _device

    path = model_path or MODEL_PATH

    # ---- 1. Verify file exists ----
    if not os.path.isfile(path):
        raise FileNotFoundError(
            f"\n{'='*60}\n"
            f"MODEL NOT FOUND\n"
            f"{'='*60}\n"
            f"Expected model at:\n"
            f"  {path}\n\n"
            f"The trained Faster R-CNN checkpoint (~500 MB) must be\n"
            f"accessible at this path.\n\n"
            f"To fix:\n"
            f"  1. Verify the file exists on your machine.\n"
            f"  2. Set the FABRIC_MODEL_PATH environment variable:\n"
            f"       set FABRIC_MODEL_PATH=C:\\path\\to\\best_model.pth\n"
            f"{'='*60}"
        )

    file_size_bytes = os.path.getsize(path)
    file_size_mb = file_size_bytes / (1024 * 1024)

    import hashlib
    sha256 = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(8192 * 1024):
            sha256.update(chunk)
    ckpt_hash = sha256.hexdigest()

    logger.info("Model file: %s", path)
    logger.info("  File size : %d bytes (%.2f MB)", file_size_bytes, file_size_mb)
    logger.info("  SHA256    : %s", ckpt_hash)

    # ---- 2. Detect device ----
    _device = _detect_device()

    # ---- 3. Load checkpoint ----
    logger.info("Loading checkpoint...")
    t0 = time.time()

    try:
        checkpoint = torch.load(path, map_location=_device, weights_only=False)
    except Exception as e:
        raise RuntimeError(
            f"Failed to load checkpoint from {path}\n"
            f"Error: {e}\n\n"
            f"The file may be corrupted or incompatible with this PyTorch version."
        ) from e

    load_time = time.time() - t0
    logger.info("Checkpoint loaded in %.2f s", load_time)

    # ---- 4. Inspect checkpoint ----
    if not isinstance(checkpoint, dict):
        raise RuntimeError(
            f"Unexpected checkpoint type: {type(checkpoint).__name__}. "
            f"Expected a dict with 'model' key containing the state_dict."
        )

    # Determine if the checkpoint stores model state_dict in "model" key
    if "model" in checkpoint:
        state_dict = checkpoint["model"]
    else:
        # Fallback: treat the whole dict as a state_dict
        state_dict = checkpoint
        logger.warning(
            "Checkpoint has no 'model' key — treating entire dict as state_dict."
        )

    # Extract metadata from checkpoint
    ckpt_config = checkpoint.get("config", {})
    ckpt_class_names = checkpoint.get("class_names", None)
    ckpt_num_classes = ckpt_config.get("num_classes", None)
    ckpt_epoch = checkpoint.get("epoch", "unknown")
    ckpt_best = checkpoint.get("best", {})

    logger.info("Checkpoint metadata:")
    logger.info("  epoch        : %s", ckpt_epoch)
    logger.info("  num_classes  : %s", ckpt_num_classes)
    logger.info("  class_names  : %s", ckpt_class_names)
    if ckpt_best:
        logger.info("  best mAP@50  : %.2f%%", 100 * ckpt_best.get("map50", 0))
        logger.info("  best F1      : %.2f%%", 100 * ckpt_best.get("f1", 0))

    # ---- 5. Validate class count from checkpoint ----
    # Auto-detect num_classes from the classifier weight shape
    cls_weight_key = "roi_heads.box_predictor.cls_score.weight"
    if cls_weight_key in state_dict:
        detected_num_classes = state_dict[cls_weight_key].shape[0]
        logger.info(
            "  classes (from weight shape): %d", detected_num_classes
        )
        if detected_num_classes != NUM_CLASSES:
            raise RuntimeError(
                f"\n{'='*60}\n"
                f"CLASS COUNT MISMATCH\n"
                f"{'='*60}\n"
                f"Checkpoint classifier has {detected_num_classes} output classes\n"
                f"but config.NUM_CLASSES = {NUM_CLASSES}.\n\n"
                f"This likely means the checkpoint was trained with a\n"
                f"different number of classes. Check whether the model\n"
                f"uses the legacy 5-class config (with 'line') or the\n"
                f"current 4-class config (hole, knot, stain + background).\n"
                f"{'='*60}"
            )
    else:
        logger.warning(
            "Could not find '%s' in state_dict — skipping class count verification.",
            cls_weight_key,
        )

    # ---- 6. Build architecture and load weights ----
    _model = _build_architecture(NUM_CLASSES, _device)

    try:
        _model.load_state_dict(state_dict, strict=True)
    except RuntimeError as e:
        raise RuntimeError(
            f"State dict keys do not match the expected architecture.\n"
            f"Error: {e}\n\n"
            f"This can happen if the checkpoint was trained with different\n"
            f"anchor sizes, aspect ratios, or backbone configuration.\n"
            f"Check the training notebook for the exact architecture."
        ) from e

    # ---- 7. Set to evaluation mode ----
    _model.eval()

    # ---- 8. Determine class mapping ----
    if ckpt_class_names is not None:
        # Convert string keys to int if needed (JSON serialisation quirk)
        _class_names = {int(k): v for k, v in ckpt_class_names.items()}
    else:
        _class_names = CLASS_NAMES.copy()

    logger.info("Model loaded successfully:")
    logger.info("  Architecture  : Faster R-CNN + ResNet-50 FPN")
    logger.info("  Classes       : %s", _class_names)
    logger.info("  Device        : %s", _device)
    logger.info("  Parameters    : %.1f M", sum(p.numel() for p in _model.parameters()) / 1e6)
    logger.info("  Eval mode     : True")

    return _model, _class_names, _device
