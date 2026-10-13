"""
Fabric AI Inspection System - Detection Visualizer
===================================================

Visualizes defect detections on fabric images:
- Draws bounding boxes with class-specific colors
- Displays class names and confidence percentages
- Draws defect count summary badge
- Saves annotated images to disk
"""

import os
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from typing import Any

from backend.app.config import CLASS_COLORS, RESULTS_DIR


def _get_font(size: int = 14):
    """Attempt to load a clean TTF font, falling back to PIL default."""
    font_candidates = [
        "arial.ttf",
        "segoeui.ttf",
        "tahoma.ttf",
        "DejaVuSans.ttf",
        "C:\\Windows\\Fonts\\arial.ttf",
        "C:\\Windows\\Fonts\\segoeui.ttf",
    ]
    for candidate in font_candidates:
        try:
            return ImageFont.truetype(candidate, size)
        except Exception:
            continue
    return ImageFont.load_default()


def visualize_detections(
    image_path: str,
    detections: list[dict[str, Any]],
    output_path: str | None = None,
    line_thickness: int = 3,
) -> str:
    """
    Draw bounding boxes and labels onto the fabric image and save it.

    Args:
        image_path: Path to the original input image.
        detections: List of detection dicts containing 'class', 'confidence', 'bbox'.
        output_path: Optional destination path. If None, saves in RESULTS_DIR.
        line_thickness: Bounding box line thickness.

    Returns:
        output_path of the saved annotated image.
    """
    if not os.path.isfile(image_path):
        raise FileNotFoundError(f"Image not found for visualization: {image_path}")

    # Load with PIL for crisp antialiased text & boxes
    pil_image = Image.open(image_path).convert("RGBA")
    w, h = pil_image.size

    # Create an overlay for semi-transparent highlights
    overlay = Image.new("RGBA", pil_image.size, (255, 255, 255, 0))
    draw_overlay = ImageDraw.Draw(overlay)
    draw_base = ImageDraw.Draw(pil_image)

    font = _get_font(max(13, int(min(w, h) * 0.022)))
    badge_font = _get_font(max(14, int(min(w, h) * 0.025)))

    # Color palette fallback (R, G, B)
    default_colors = {
        "hole": (244, 67, 54),       # Bright Red
        "knot": (33, 150, 243),      # Vivid Blue / Cyan
        "stain": (156, 39, 176),     # Purple / Magenta
    }

    # Draw each detection
    for idx, det in enumerate(detections, start=1):
        cls_name = det.get("class", "defect").lower()
        conf = det.get("confidence", 0.0)
        bbox = det.get("bbox", [0, 0, 0, 0])

        x1, y1, x2, y2 = [float(coord) for coord in bbox]
        x1, x2 = max(0, min(x1, w - 1)), max(0, min(x2, w - 1))
        y1, y2 = max(0, min(y1, h - 1)), max(0, min(y2, h - 1))

        color = CLASS_COLORS.get(det.get("label", 0), default_colors.get(cls_name, (255, 165, 0)))

        # Semi-transparent fill
        draw_overlay.rectangle(
            [x1, y1, x2, y2],
            fill=(color[0], color[1], color[2], 40),
            outline=None,
        )

        # Crisp bounding box on base image
        draw_base.rectangle(
            [x1, y1, x2, y2],
            outline=(color[0], color[1], color[2], 255),
            width=line_thickness,
        )

        # Label pill
        label_text = f"#{idx} {cls_name.upper()} {conf*100:.1f}%"
        bbox_text = font.getbbox(label_text)
        text_w = bbox_text[2] - bbox_text[0]
        text_h = bbox_text[3] - bbox_text[1]

        pill_padding_x = 6
        pill_padding_y = 3
        pill_y1 = max(0, y1 - text_h - pill_padding_y * 2)
        pill_y2 = pill_y1 + text_h + pill_padding_y * 2
        pill_x1 = x1
        pill_x2 = min(w, x1 + text_w + pill_padding_x * 2)

        # Pill background
        draw_base.rounded_rectangle(
            [pill_x1, pill_y1, pill_x2, pill_y2],
            radius=4,
            fill=(color[0], color[1], color[2], 230),
        )

        # Text in white
        draw_base.text(
            (pill_x1 + pill_padding_x, pill_y1 + pill_padding_y - 1),
            label_text,
            font=font,
            fill=(255, 255, 255, 255),
        )

    # Composite overlay
    annotated = Image.alpha_composite(pil_image, overlay).convert("RGB")
    draw_final = ImageDraw.Draw(annotated)

    # Top-right summary watermark badge
    summary_text = f"Defects Detected: {len(detections)}"
    sum_bbox = badge_font.getbbox(summary_text)
    badge_w = sum_bbox[2] - sum_bbox[0] + 16
    badge_h = sum_bbox[3] - sum_bbox[1] + 10
    badge_x = w - badge_w - 12
    badge_y = 12

    badge_bg = (239, 68, 68) if len(detections) > 0 else (16, 185, 129)
    draw_final.rounded_rectangle(
        [badge_x, badge_y, badge_x + badge_w, badge_y + badge_h],
        radius=6,
        fill=badge_bg,
    )
    draw_final.text(
        (badge_x + 8, badge_y + 4),
        summary_text,
        font=badge_font,
        fill=(255, 255, 255),
    )

    # Save output
    if output_path is None:
        os.makedirs(RESULTS_DIR, exist_ok=True)
        base_name = os.path.splitext(os.path.basename(image_path))[0]
        output_path = os.path.join(RESULTS_DIR, f"{base_name}_annotated.jpg")
    else:
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    annotated.save(output_path, "JPEG", quality=95)
    return output_path
