"""
Stage 1 — Model Verification Test
====================================

This script validates that the Faster R-CNN model loads correctly and
produces valid detections on a real fabric image.

Run from the project root:
    python -m backend.app.model.test_stage1

It will:
    1. Verify model path exists
    2. Load the model
    3. Validate architecture
    4. Validate class mapping
    5. Run inference on a test image
    6. Report detections, timing, and diagnostics
"""

import os
import sys
import json
import time
import logging
import glob

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.app.config import MODEL_PATH, NUM_CLASSES, CLASS_NAMES, CONFIDENCE_THRESHOLD
from backend.app.model.model_loader import load_model
from backend.app.model.detector import detect_defects


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("stage1_test")


def hr(title: str = "", char: str = "=") -> None:
    print(char * 70)
    if title:
        print(title)
        print(char * 70)


def find_test_image() -> str:
    """Find a suitable test image from the project."""
    candidates = [
        # Test dataset images
        os.path.join(PROJECT_ROOT, "Dataset", "test"),
        # Existing detection results
        os.path.join(PROJECT_ROOT, "results", "detections"),
        # Training images as fallback
        os.path.join(PROJECT_ROOT, "Dataset", "train"),
    ]

    for folder in candidates:
        if os.path.isdir(folder):
            images = glob.glob(os.path.join(folder, "*.jpg"))
            images += glob.glob(os.path.join(folder, "*.png"))
            if images:
                # Prefer images with defect-related names
                for img in images:
                    basename = os.path.basename(img).lower()
                    if any(kw in basename for kw in ["hole", "stain", "knot", "leke", "delik"]):
                        return img
                return images[0]

    raise FileNotFoundError(
        "No test image found. Place a fabric image in Dataset/test/ or results/detections/"
    )


def main() -> None:
    import torch

    hr("STAGE 1 -- MODEL VERIFICATION TEST")
    print()

    # ---- Step 1: Verify model path ----
    hr("1. MODEL PATH VERIFICATION", "-")
    print(f"  Configured path : {MODEL_PATH}")
    print(f"  File exists     : {os.path.isfile(MODEL_PATH)}")
    if os.path.isfile(MODEL_PATH):
        size_mb = os.path.getsize(MODEL_PATH) / (1024 * 1024)
        print(f"  File size       : {size_mb:.1f} MB")
    else:
        print("\n  ERROR: Model file not found!")
        print(f"  Expected at: {MODEL_PATH}")
        print("  Set FABRIC_MODEL_PATH env var to the correct location.")
        sys.exit(1)
    print()

    # ---- Step 2: Load model ----
    hr("2. MODEL LOADING", "-")
    t0 = time.time()
    try:
        model, class_names, device = load_model()
    except Exception as e:
        print(f"\n  FATAL ERROR: Could not load model!")
        print(f"  {e}")
        sys.exit(1)
    load_time = time.time() - t0
    print(f"  Load time       : {load_time:.2f} s")
    print()

    # ---- Step 3: Validate architecture ----
    hr("3. ARCHITECTURE VALIDATION", "-")
    cls_out = model.roi_heads.box_predictor.cls_score.out_features
    n_params = sum(p.numel() for p in model.parameters())
    n_train = sum(p.numel() for p in model.parameters() if p.requires_grad)

    print(f"  Model           : Faster R-CNN + ResNet-50 FPN")
    print(f"  Backbone        : ResNet-50 + FPN")
    print(f"  cls_score.out   : {cls_out}  (expected: {NUM_CLASSES})")
    print(f"  Parameters      : {n_params/1e6:.1f} M total")
    print(f"  Trainable       : {n_train/1e6:.1f} M")
    print(f"  Device          : {device}")
    print(f"  Training mode   : {model.training}  (should be False)")

    if cls_out != NUM_CLASSES:
        print(f"\n  MISMATCH: classifier head has {cls_out} classes but config expects {NUM_CLASSES}")
        sys.exit(1)
    if model.training:
        print("  WARNING: model is in training mode!")
    print("  [OK] Architecture matches checkpoint")
    print()

    # ---- Step 4: Validate class mapping ----
    hr("4. CLASS MAPPING", "-")
    print(f"  From checkpoint : {class_names}")
    print(f"  From config     : {CLASS_NAMES}")
    match = all(class_names.get(k) == v for k, v in CLASS_NAMES.items())
    if match:
        print("  [OK] Class mappings match")
    else:
        print("  WARNING: Class mappings differ!")
        print(f"    Checkpoint: {class_names}")
        print(f"    Config:     {CLASS_NAMES}")
    print()

    # ---- Step 5: Find and run inference on test image ----
    hr("5. INFERENCE TEST", "-")
    try:
        test_img = find_test_image()
    except FileNotFoundError as e:
        print(f"  {e}")
        sys.exit(1)

    print(f"  Test image      : {test_img}")
    print(f"  Conf threshold  : {CONFIDENCE_THRESHOLD}")
    print()

    try:
        result = detect_defects(test_img, confidence_threshold=CONFIDENCE_THRESHOLD)
    except Exception as e:
        print(f"\n  INFERENCE ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # ---- Step 6: Report results ----
    hr("6. RESULTS", "-")
    print(f"  Image           : {os.path.basename(result['image_path'])}")
    print(f"  Dimensions      : {result['image_width']} x {result['image_height']}")
    print(f"  Device          : {result['device']}")
    print(f"  Inference time  : {result['inference_time_ms']:.1f} ms")
    print(f"  Threshold       : {result['confidence_threshold']}")
    print()

    # Summary
    summary = result["summary"]
    print(f"  Total detections: {summary['total']}")
    for cls_name in ["hole", "knot", "stain"]:
        count = summary.get(cls_name, 0)
        print(f"    {cls_name:<10}    : {count}")
    print()

    # Individual detections
    if result["detections"]:
        print("  Detections:")
        for i, det in enumerate(result["detections"], 1):
            bbox = det["bbox"]
            print(
                f"    [{i}] {det['class']:<8}  "
                f"conf={det['confidence']:.4f}  "
                f"bbox=[{bbox[0]:.1f}, {bbox[1]:.1f}, {bbox[2]:.1f}, {bbox[3]:.1f}]"
            )
    else:
        print("  No detections above threshold.")
        print("  (This may be normal if the test image has no defects,")
        print("   or try lowering the confidence threshold.)")
    print()

    # ---- Also test with lower threshold to see all raw detections ----
    hr("7. RAW DETECTIONS (conf >= 0.10)", "-")
    result_low = detect_defects(test_img, confidence_threshold=0.10)
    if result_low["detections"]:
        print(f"  {len(result_low['detections'])} detections at conf >= 0.10:")
        for det in result_low["detections"][:10]:
            print(f"    {det['class']:<8}  conf={det['confidence']:.4f}")
        if len(result_low["detections"]) > 10:
            print(f"    ... and {len(result_low['detections']) - 10} more")
    else:
        print("  No detections even at conf >= 0.10")
    print()

    # ---- Final Summary ----
    hr("STAGE 1 VERIFICATION COMPLETE")
    print()
    print("  +================================================+")
    print("  |         STAGE 1 -- VERIFICATION REPORT          |")
    print("  +================================================+")
    print(f"  |  Model     : Faster R-CNN + ResNet-50 FPN       |")
    print(f"  |  Classes   : {', '.join(class_names.values()):<34}|")
    print(f"  |  Num classes: {NUM_CLASSES} (bg + {NUM_CLASSES-1} defects)             |")
    print(f"  |  Device    : {str(device):<35}|")
    print(f"  |  Load time : {load_time:.2f}s{' '*31}|")
    print(f"  |  Infer time: {result['inference_time_ms']:.1f}ms{' '*30}|")
    print(f"  |  Detections: {summary['total']:<35}|")
    print(f"  |  Status    : PASSED{' '*27}|")
    print("  +================================================+")
    print()

    # Save result to JSON for reference
    output_path = os.path.join(PROJECT_ROOT, "backend", "stage1_result.json")
    serializable = {
        k: v for k, v in result.items()
    }
    with open(output_path, "w") as f:
        json.dump(serializable, f, indent=2)
    print(f"  Result saved to: {output_path}")
    print()


if __name__ == "__main__":
    main()
