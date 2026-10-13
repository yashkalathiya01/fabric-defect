"""
Model Diagnostic Tool: Evaluate Faster R-CNN on Fabric and Non-Fabric Categories
================================================================================

Directly loads the authoritative checkpoint `E:\Project\models\object detection\best_model.pth`
and evaluates raw and filtered detections across:
  A. Known fabric image containing defects
  B. Known fabric image without defects
  C. Random non-fabric image
  D. Person image
  E. Animal image
  F. Document/paper image

Annotated detection outputs are saved to `outputs/diagnostics/`.
"""

import os
import sys
import hashlib
import time
import numpy as np
import torch
import torchvision
from torchvision.models.detection.faster_rcnn import FastRCNNPredictor
from PIL import Image, ImageDraw

# Set paths
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

CKPT_PATH = r"E:\Project\models\object detection\best_model.pth"
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "outputs", "diagnostics")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Colors for bounding boxes
CLASS_COLORS = {
    1: (255, 60, 60),    # hole -> Red
    2: (0, 200, 255),    # knot -> Cyan
    3: (180, 100, 255),  # stain -> Purple
}


def compute_sha256(filepath: str) -> str:
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(8192 * 1024):
            sha256.update(chunk)
    return sha256.hexdigest()


def load_authoritative_model():
    print("=" * 70)
    print("PHASE 3: LOADING AUTHORITATIVE CHECKPOINT")
    print("=" * 70)
    if not os.path.isfile(CKPT_PATH):
        raise FileNotFoundError(f"Checkpoint not found at: {CKPT_PATH}")

    file_size = os.path.getsize(CKPT_PATH)
    sha256_hash = compute_sha256(CKPT_PATH)

    print(f"Checkpoint path: {CKPT_PATH}")
    print(f"File size      : {file_size} bytes ({file_size / (1024*1024):.2f} MB)")
    print(f"SHA256         : {sha256_hash}")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Inference device: {device}")

    # Build exact architecture matching checkpoint
    model = torchvision.models.detection.fasterrcnn_resnet50_fpn(
        weights=None,
        weights_backbone=None,
        min_size=800,
        max_size=1333,
        box_detections_per_img=100,
        box_score_thresh=0.01,
        trainable_backbone_layers=5,
    )
    in_features = model.roi_heads.box_predictor.cls_score.in_features
    model.roi_heads.box_predictor = FastRCNNPredictor(in_features, 4)

    # Load weights
    data = torch.load(CKPT_PATH, map_location=device)
    state_dict = data["model"] if isinstance(data, dict) and "model" in data else data
    model.load_state_dict(state_dict, strict=True)
    model.to(device)
    model.eval()

    class_names = data.get("class_names", {1: "hole", 2: "knot", 3: "stain"})
    if isinstance(class_names, dict):
        class_names = {int(k): v for k, v in class_names.items()}

    print(f"Model architecture: Faster R-CNN + ResNet-50 FPN")
    print(f"Classes           : {class_names}")
    print(f"Evaluation mode   : {not model.training}")
    print("=" * 70 + "\n")

    return model, class_names, device


def run_diagnostic_on_image(
    model,
    class_names: dict,
    device: torch.device,
    image_path: str,
    output_filename: str,
    category_label: str,
    conf_threshold: float = 0.50,
):
    print(f"\n>>> TEST CATEGORY: {category_label}")
    print(f"filename: {os.path.basename(image_path)}")

    if not os.path.isfile(image_path):
        print(f"  [ERROR] Image file not found: {image_path}")
        return

    pil_img = Image.open(image_path).convert("RGB")
    w, h = pil_img.size
    print(f"image dimensions: {w}x{h}")
    print(f"model: Faster R-CNN + ResNet-50 FPN")
    print(f"device: {device}")

    # Prepare tensor
    img_np = np.array(pil_img, dtype=np.uint8)
    tensor = torch.from_numpy(img_np).permute(2, 0, 1).float() / 255.0
    tensor = tensor.to(device)

    t0 = time.time()
    with torch.inference_mode():
        outputs = model([tensor])
    elapsed_ms = (time.time() - t0) * 1000.0

    out = outputs[0]
    boxes = out["boxes"].cpu().numpy()
    scores = out["scores"].cpu().numpy()
    labels = out["labels"].cpu().numpy()

    num_raw = len(scores)
    keep = scores >= conf_threshold
    filtered_boxes = boxes[keep]
    filtered_scores = scores[keep]
    filtered_labels = labels[keep]
    num_filtered = len(filtered_scores)

    print(f"inference time: {elapsed_ms:.1f} ms")
    print(f"number of raw detections: {num_raw}")
    print(f"number of detections after filtering (threshold >= {conf_threshold:.2f}): {num_filtered}")

    if num_filtered == 0:
        print("  -> No detections meeting the threshold.")
    else:
        for idx, (b, s, l) in enumerate(zip(filtered_boxes, filtered_scores, filtered_labels)):
            c_name = class_names.get(int(l), f"class_{l}")
            bbox_str = f"[{b[0]:.1f}, {b[1]:.1f}, {b[2]:.1f}, {b[3]:.1f}]"
            print(f"  [{idx+1}] class: {c_name:<6} | confidence: {s:.4f} ({s*100:.1f}%) | bounding box: {bbox_str}")

    # Draw annotated image
    annotated = pil_img.copy()
    draw = ImageDraw.Draw(annotated)

    for b, s, l in zip(filtered_boxes, filtered_scores, filtered_labels):
        c_name = class_names.get(int(l), f"class_{l}")
        color = CLASS_COLORS.get(int(l), (255, 255, 0))
        # Draw box
        draw.rectangle([b[0], b[1], b[2], b[3]], outline=color, width=3)
        # Draw label banner
        tag = f"{c_name.upper()} {s*100:.1f}%"
        draw.rectangle([b[0], max(0, b[1] - 18), b[0] + len(tag) * 8 + 6, max(0, b[1])], fill=color)
        draw.text((b[0] + 3, max(0, b[1] - 16)), tag, fill=(255, 255, 255))

    out_path = os.path.join(OUTPUT_DIR, output_filename)
    annotated.save(out_path, quality=95)
    print(f"Saved annotated output to: {out_path}")


def main():
    model, class_names, device = load_authoritative_model()

    samples = [
        {
            "cat": "A. Known fabric image containing defects",
            "path": r"E:\Project\data\test_samples\fabric_defect.jpg",
            "out": "fabric_defect.jpg",
        },
        {
            "cat": "B. Known fabric image without defects",
            "path": r"E:\Project\data\test_samples\fabric_clean.jpg",
            "out": "fabric_clean.jpg",
        },
        {
            "cat": "C. Random non-fabric image (street / bus)",
            "path": r"E:\Project\data\test_samples\street_bus.jpg",
            "out": "random_scene.jpg",
        },
        {
            "cat": "D. Person image (person wearing clothes / kurta)",
            "path": r"E:\Project\data\test_samples\person_kurta.jpg",
            "out": "person.jpg",
        },
        {
            "cat": "E. Animal image (dog)",
            "path": r"E:\Project\data\test_samples\animal_dog.jpg",
            "out": "animal.jpg",
        },
        {
            "cat": "F. Document / paper image",
            "path": r"E:\Project\data\test_samples\document_paper.jpg",
            "out": "document.jpg",
        },
    ]

    for s in samples:
        run_diagnostic_on_image(
            model=model,
            class_names=class_names,
            device=device,
            image_path=s["path"],
            output_filename=s["out"],
            category_label=s["cat"],
            conf_threshold=0.50,
        )

    print("\n" + "=" * 70)
    print(f"ALL DIAGNOSTICS COMPLETED. Outputs saved to: {OUTPUT_DIR}")
    print("=" * 70)


if __name__ == "__main__":
    main()
