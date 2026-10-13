"""
Validation Threshold Evaluation Tool
====================================

Evaluates Faster R-CNN performance across confidence thresholds:
[0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90, 0.95]

Computes:
  - Precision
  - Recall
  - F1 Score
  - False Positives count
  - Class-wise breakdown (hole, knot, stain)

Uses validation dataset (Dataset/valid) to determine optimal operating threshold.
"""

import os
import sys
import json
import time
import numpy as np
import torch
import torchvision
from torchvision.models.detection.faster_rcnn import FastRCNNPredictor
from PIL import Image

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

CKPT_PATH = r"E:\Project\models\object detection\best_model.pth"
VALID_DIR = r"E:\Project\Dataset\valid"
ANNOTATIONS_PATH = os.path.join(VALID_DIR, "_annotations.coco.json")

THRESHOLDS = [0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90, 0.95]
IOU_THRESHOLD = 0.50


def compute_iou(box1, box2):
    """
    Computes IoU between two boxes in [x1, y1, x2, y2] format.
    """
    x1 = max(box1[0], box2[0])
    y1 = max(box1[1], box2[1])
    x2 = min(box1[2], box2[2])
    y2 = min(box1[3], box2[3])

    inter = max(0, x2 - x1) * max(0, y2 - y1)
    area1 = (box1[2] - box1[0]) * (box1[3] - box1[1])
    area2 = (box2[2] - box2[0]) * (box2[3] - box2[1])
    union = area1 + area2 - inter

    return inter / union if union > 0 else 0.0


def load_model():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
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

    data = torch.load(CKPT_PATH, map_location=device)
    sd = data["model"] if isinstance(data, dict) and "model" in data else data
    model.load_state_dict(sd, strict=True)
    model.to(device)
    model.eval()
    return model, device


def main():
    print("=" * 80)
    print("PHASE 4: VALIDATION SET CONFIDENCE THRESHOLD EVALUATION")
    print("=" * 80)
    print(f"Loading annotations from: {ANNOTATIONS_PATH}")

    with open(ANNOTATIONS_PATH, "r") as f:
        coco = json.load(f)

    # Categories in COCO: {'id': 0, 'name': 'hole'}, {'id': 1, 'name': 'knot'}, {'id': 2, 'name': 'stain'}
    # Model classes: 1: hole, 2: knot, 3: stain
    coco_cat_to_model_label = {0: 1, 1: 2, 2: 3}
    class_names = {1: "hole", 2: "knot", 3: "stain"}

    # Map image_id -> list of GT boxes: [{'box': [x1, y1, x2, y2], 'label': int}]
    img_gt = {img["id"]: [] for img in coco["images"]}
    img_info_map = {img["id"]: img for img in coco["images"]}

    for ann in coco["annotations"]:
        bbox = ann["bbox"] # [x, y, w, h]
        x1, y1, w, h = bbox
        box = [x1, y1, x1 + w, y1 + h]
        label = coco_cat_to_model_label[ann["category_id"]]
        img_gt[ann["image_id"]].append({"box": box, "label": label})

    # Evaluate on first 60 validation images to balance thoroughness and execution time
    sample_images = coco["images"][:60]
    print(f"Evaluating detector on {len(sample_images)} validation images...")

    total_gt = sum(len(img_gt[img["id"]]) for img in sample_images)
    gt_counts = {1: 0, 2: 0, 3: 0}
    for img in sample_images:
        for ann in img_gt[img["id"]]:
            gt_counts[ann["label"]] += 1

    print(f"Ground Truth Defect Count: {total_gt} total "
          f"({gt_counts[1]} holes, {gt_counts[2]} knots, {gt_counts[3]} stains)\n")

    model, device = load_model()

    # Step 1: Run inference and cache all predictions
    print("Running inference across validation subset...")
    cached_preds = []
    t_start = time.time()

    for idx, img_info in enumerate(sample_images):
        img_path = os.path.join(VALID_DIR, img_info["file_name"])
        pil_img = Image.open(img_path).convert("RGB")
        img_np = np.array(pil_img, dtype=np.uint8)
        tensor = torch.from_numpy(img_np).permute(2, 0, 1).float() / 255.0
        tensor = tensor.to(device)

        with torch.inference_mode():
            outputs = model([tensor])

        out = outputs[0]
        boxes = out["boxes"].cpu().numpy()
        scores = out["scores"].cpu().numpy()
        labels = out["labels"].cpu().numpy()

        cached_preds.append({
            "img_id": img_info["id"],
            "boxes": boxes,
            "scores": scores,
            "labels": labels,
            "gt": img_gt[img_info["id"]],
        })

        if (idx + 1) % 15 == 0:
            print(f"  Processed {idx + 1}/{len(sample_images)} images ({time.time() - t_start:.1f} s elapsed)")

    print(f"Inference completed in {time.time() - t_start:.1f} s.\n")

    # Step 2: Evaluate across thresholds
    print("=" * 80)
    print(f"{'THRESH':<8} | {'PRECISION':<10} | {'RECALL':<10} | {'F1 SCORE':<10} | {'FP COUNT':<9} | {'TP COUNT':<9} | {'FN COUNT':<9}")
    print("-" * 80)

    results_table = []
    best_f1 = -1.0
    best_thresh = 0.50

    for thresh in THRESHOLDS:
        # Overall counters
        tp_total = 0
        fp_total = 0
        fn_total = 0

        # Per-class counters: {label: {'tp': 0, 'fp': 0, 'fn': 0}}
        class_stats = {l: {"tp": 0, "fp": 0, "fn": 0} for l in [1, 2, 3]}

        for item in cached_preds:
            gt_list = item["gt"]
            matched_gt = set()

            # Filter predictions by threshold
            keep = item["scores"] >= thresh
            p_boxes = item["boxes"][keep]
            p_scores = item["scores"][keep]
            p_labels = item["labels"][keep]

            # Sort predictions by descending score
            sort_order = np.argsort(-p_scores)
            p_boxes = p_boxes[sort_order]
            p_scores = p_scores[sort_order]
            p_labels = p_labels[sort_order]

            for p_box, p_score, p_label in zip(p_boxes, p_scores, p_labels):
                best_iou = 0.0
                best_gt_idx = -1

                for gt_idx, gt_item in enumerate(gt_list):
                    if gt_idx in matched_gt:
                        continue
                    if gt_item["label"] == p_label:
                        iou = compute_iou(p_box, gt_item["box"])
                        if iou > best_iou:
                            best_iou = iou
                            best_gt_idx = gt_idx

                if best_iou >= IOU_THRESHOLD:
                    tp_total += 1
                    class_stats[p_label]["tp"] += 1
                    matched_gt.add(best_gt_idx)
                else:
                    fp_total += 1
                    class_stats[p_label]["fp"] += 1

            # Unmatched GT are false negatives
            for gt_idx, gt_item in enumerate(gt_list):
                if gt_idx not in matched_gt:
                    fn_total += 1
                    class_stats[gt_item["label"]]["fn"] += 1

        precision = tp_total / (tp_total + fp_total) if (tp_total + fp_total) > 0 else 0.0
        recall = tp_total / (tp_total + fn_total) if (tp_total + fn_total) > 0 else 0.0
        f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

        if f1 > best_f1:
            best_f1 = f1
            best_thresh = thresh

        print(f"{thresh:<8.2f} | {precision*100:<9.1f}% | {recall*100:<9.1f}% | {f1*100:<9.1f}% | {fp_total:<9} | {tp_total:<9} | {fn_total:<9}")

        results_table.append({
            "threshold": thresh,
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "tp": tp_total,
            "fp": fp_total,
            "fn": fn_total,
            "per_class": class_stats,
        })

    print("-" * 80)
    print(f"\n[OPTIMAL VALIDATION OPERATING THRESHOLD]: {best_thresh:.2f} (Peak F1: {best_f1*100:.2f}%)\n")

    # Print Class-wise Breakdown at Optimal Threshold
    opt_res = next(r for r in results_table if r["threshold"] == best_thresh)
    print("=" * 80)
    print(f"CLASS-WISE BREAKDOWN AT OPTIMAL THRESHOLD ({best_thresh:.2f}):")
    print("=" * 80)
    print(f"{'CLASS':<10} | {'PRECISION':<10} | {'RECALL':<10} | {'F1':<10} | {'TP':<6} | {'FP':<6} | {'FN':<6}")
    print("-" * 80)

    for l, name in class_names.items():
        st = opt_res["per_class"][l]
        p = st["tp"] / (st["tp"] + st["fp"]) if (st["tp"] + st["fp"]) > 0 else 0.0
        r = st["tp"] / (st["tp"] + st["fn"]) if (st["tp"] + st["fn"]) > 0 else 0.0
        f1_cls = (2 * p * r) / (p + r) if (p + r) > 0 else 0.0
        print(f"{name:<10} | {p*100:<9.1f}% | {r*100:<9.1f}% | {f1_cls*100:<9.1f}% | {st['tp']:<6} | {st['fp']:<6} | {st['fn']:<6}")

    print("=" * 80)


if __name__ == "__main__":
    main()
