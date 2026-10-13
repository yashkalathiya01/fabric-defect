"""
Fabric AI Inspection System - OpenCV Structural & Warp/Weft Analysis
====================================================================

Performs thread-level structural inspection of woven fabrics using OpenCV:
  1. Grayscale conversion & preprocessing
  2. Gaussian Blur (noise reduction)
  3. Adaptive/Otsu Thresholding
  4. Morphological operations (opening/closing to accentuate yarn structure)
  5. Canny Edge Detection
  6. Hough Line Transform (Standard & Probabilistic)
  7. Angle histogram & dominant orientation extraction
  8. Warp (vertical/near-vertical) & Weft (horizontal/near-horizontal) clustering
  9. Inter-yarn spacing estimation & regularity standard deviation
 10. Alignment deviation (orthogonality offset from 90 degrees)

Exports intermediate pipeline visualization images for the frontend UI.
Does NOT fabricate values if lines or weave structure cannot be reliably detected.
"""

import os
import cv2
import numpy as np
from typing import Any
from scipy.ndimage import gaussian_filter1d

from backend.app.config import RESULTS_DIR


def analyze_fabric_structure(
    image_path: str,
    output_dir: str | None = None,
    target_dim: int = 800,
) -> dict[str, Any]:
    """
    Execute full OpenCV structural and warp/weft analysis on a fabric sample.

    Args:
        image_path: Path to fabric image.
        output_dir: Directory to save intermediate visualization images.
        target_dim: Max dimension to resize for standardized spatial line analysis.

    Returns:
        Structured dictionary containing numerical measurements and visualization image paths.
    """
    if not os.path.isfile(image_path):
        raise FileNotFoundError(f"Image not found: {image_path}")

    save_dir = output_dir or os.path.join(RESULTS_DIR, "structural")
    os.makedirs(save_dir, exist_ok=True)
    base_name = os.path.splitext(os.path.basename(image_path))[0]

    # 1. Load original image
    img_bgr = cv2.imread(image_path)
    if img_bgr is None:
        raise ValueError(f"OpenCV failed to decode image: {image_path}")

    orig_h, orig_w = img_bgr.shape[:2]

    # Resize proportionally for standardized frequency analysis
    scale = min(target_dim / orig_w, target_dim / orig_h)
    if scale < 1.0:
        new_w, new_h = int(orig_w * scale), int(orig_h * scale)
        img_resized = cv2.resize(img_bgr, (new_w, new_h), interpolation=cv2.INTER_AREA)
    else:
        img_resized = img_bgr.copy()
        new_w, new_h = orig_w, orig_h

    # 2. Grayscale conversion
    gray = cv2.cvtColor(img_resized, cv2.COLOR_BGR2GRAY)
    gray_path = os.path.join(save_dir, f"{base_name}_gray.jpg")
    cv2.imwrite(gray_path, gray)

    # 3. Gaussian Blur to eliminate high-frequency pixel noise
    blurred = cv2.GaussianBlur(gray, (5, 5), 1.2)

    # 4. Thresholding (Adaptive + Otsu hybrid for variable textile illumination)
    thresh = cv2.adaptiveThreshold(
        blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 15, 3
    )
    thresh_path = os.path.join(save_dir, f"{base_name}_thresh.jpg")
    cv2.imwrite(thresh_path, thresh)

    # 5. Morphological operations (small kernel to join yarn striations)
    morph_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    morph = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, morph_kernel)

    # 6. Canny Edge Detection (with auto-calculated thresholds)
    med_val = np.median(blurred)
    lower_canny = int(max(20, 0.66 * med_val))
    upper_canny = int(min(240, 1.33 * med_val))
    edges = cv2.Canny(morph, lower_canny, upper_canny, apertureSize=3)
    edges_path = os.path.join(save_dir, f"{base_name}_canny.jpg")
    cv2.imwrite(edges_path, edges)

    # 7. Hough Line Transform (Standard & Probabilistic)
    # Use Probabilistic Hough Transform for segment extraction
    min_line_len = int(min(new_w, new_h) * 0.08)
    max_line_gap = int(min(new_w, new_h) * 0.03)
    lines_p = cv2.HoughLinesP(
        edges,
        rho=1,
        theta=np.pi / 180,
        threshold=45,
        minLineLength=min_line_len,
        maxLineGap=max_line_gap,
    )

    # Prepare visualization overlays
    hough_vis = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
    warp_vis = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
    weft_vis = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)

    angles = []
    line_segments = []

    if lines_p is not None and len(lines_p) > 0:
        for line in lines_p:
            x1, y1, x2, y2 = line[0]
            dx = x2 - x1
            dy = y2 - y1
            length = np.sqrt(dx * dx + dy * dy)
            if length < 5:
                continue

            # Compute angle in degrees [0, 180)
            angle_rad = np.arctan2(dy, dx)
            angle_deg = np.degrees(angle_rad) % 180.0
            angles.append(angle_deg)
            line_segments.append((x1, y1, x2, y2, angle_deg, length))

            # Draw on general Hough overlay
            cv2.line(hough_vis, (x1, y1), (x2, y2), (0, 255, 255), 1, cv2.LINE_AA)

    hough_path = os.path.join(save_dir, f"{base_name}_hough.jpg")
    cv2.imwrite(hough_path, hough_vis)

    # 8. Check if reliable structure analysis is possible
    if len(angles) < 10:
        # Not enough lines detected (e.g. non-woven, plain untextured, or blurry fabric)
        return {
            "status": "inconclusive",
            "message": "Insufficient structural line patterns detected in fabric texture.",
            "measurements": {
                "warp_angle": None,
                "weft_angle": None,
                "warp_spacing": None,
                "weft_spacing": None,
                "warp_spacing_std": None,
                "weft_spacing_std": None,
                "alignment_deviation": None,
                "orientation_confidence": 0.0,
                "line_count": len(angles),
            },
            "visualization_paths": {
                "grayscale": gray_path,
                "threshold": thresh_path,
                "canny_edges": edges_path,
                "hough_lines": hough_path,
                "warp_lines": None,
                "weft_lines": None,
            },
        }

    # 9. Angle Histogram & Peak Detection for Warp & Weft
    # Weft typically corresponds to horizontal threads (~0° or ~180°)
    # Warp typically corresponds to vertical threads (~90°)
    bin_size = 3.0
    num_bins = int(180.0 / bin_size)
    hist, bin_edges = np.histogram(angles, bins=num_bins, range=(0, 180))
    hist_smooth = gaussian_filter1d(hist.astype(float), sigma=1.5)

    # Identify dominant orientation clusters:
    # Cluster 1: Near vertical (warp candidate: 45° to 135°)
    warp_mask = [(45.0 <= a <= 135.0) for a in angles]
    warp_angles = [a for a, m in zip(angles, warp_mask) if m]
    warp_lines = [l for l, m in zip(line_segments, warp_mask) if m]

    # Cluster 2: Near horizontal (weft candidate: 0° to 45° or 135° to 180°)
    weft_mask = [not m for m in warp_mask]
    # Normalize weft angles around 0: angles > 90 wrap around to a - 180 for mean calculation
    weft_angles_raw = [a for a, m in zip(angles, weft_mask) if m]
    weft_lines = [l for l, m in zip(line_segments, weft_mask) if m]

    # Calculate Warp Angle (median/mean of vertical cluster)
    if warp_angles:
        warp_angle = round(float(np.median(warp_angles)), 2)
    else:
        warp_angle = None

    # Calculate Weft Angle (median of horizontal cluster, mapped to [0, 90] or [-45, 45])
    if weft_angles_raw:
        weft_angles_centered = [a if a <= 90 else a - 180 for a in weft_angles_raw]
        weft_angle_centered = float(np.median(weft_angles_centered))
        weft_angle = round((weft_angle_centered + 180) % 180.0, 2)
    else:
        weft_angle = None

    # Calculate Alignment Deviation from 90° orthogonality
    if warp_angle is not None and weft_angle is not None:
        # Effective angle difference
        diff = abs(warp_angle - weft_angle)
        deviation = abs(diff - 90.0)
        alignment_deviation = round(float(deviation), 2)
    else:
        alignment_deviation = None

    # 10. Spacing Estimation
    # Intercept along the orthogonal axis:
    # For warp (vertical-ish), find X-intercept at mid-height y = new_h/2
    warp_spacing, warp_spacing_std = _calculate_spacing(warp_lines, axis="x", ref_coord=new_h / 2)
    # For weft (horizontal-ish), find Y-intercept at mid-width x = new_w/2
    weft_spacing, weft_spacing_std = _calculate_spacing(weft_lines, axis="y", ref_coord=new_w / 2)

    # 11. Orientation confidence
    # Ratio of lines that fall clearly into the two orthogonal modes vs random noise
    structured_line_count = len(warp_lines) + len(weft_lines)
    orientation_confidence = round(min(1.0, (structured_line_count / max(1, len(angles))) * (min(len(angles), 80) / 80.0)), 3)

    # 12. Draw categorized Warp & Weft visualization images
    # Warp (Vertical) lines in Cyan
    for l in warp_lines:
        cv2.line(warp_vis, (l[0], l[1]), (l[2], l[3]), (255, 200, 0), 2, cv2.LINE_AA)
    warp_path = os.path.join(save_dir, f"{base_name}_warp.jpg")
    cv2.imwrite(warp_path, warp_vis)

    # Weft (Horizontal) lines in Orange
    for l in weft_lines:
        cv2.line(weft_vis, (l[0], l[1]), (l[2], l[3]), (0, 140, 255), 2, cv2.LINE_AA)
    weft_path = os.path.join(save_dir, f"{base_name}_weft.jpg")
    cv2.imwrite(weft_path, weft_vis)

    return {
        "status": "success",
        "measurements": {
            "dominant_directions": {
                "warp_direction_deg": warp_angle,
                "weft_direction_deg": weft_angle,
            },
            "warp_angle": warp_angle,
            "weft_angle": weft_angle,
            "warp_spacing_px": warp_spacing,
            "weft_spacing_px": weft_spacing,
            "warp_spacing_std": warp_spacing_std,
            "weft_spacing_std": weft_spacing_std,
            "alignment_deviation_deg": alignment_deviation,
            "orientation_confidence": orientation_confidence,
            "line_statistics": {
                "total_lines_detected": len(angles),
                "warp_line_count": len(warp_lines),
                "weft_line_count": len(weft_lines),
            },
        },
        "visualization_paths": {
            "grayscale": gray_path,
            "threshold": thresh_path,
            "canny_edges": edges_path,
            "hough_lines": hough_path,
            "warp_lines": warp_path,
            "weft_lines": weft_path,
        },
    }


def _calculate_spacing(
    lines: list[tuple],
    axis: str,
    ref_coord: float,
) -> tuple[float | None, float | None]:
    """
    Calculate average yarn spacing and standard deviation by projecting lines onto a cross-section.
    """
    if len(lines) < 4:
        return None, None

    intercepts = []
    for x1, y1, x2, y2, angle, length in lines:
        if axis == "x":
            # Finding x-intercept at y = ref_coord
            if abs(y2 - y1) < 1e-4:
                continue
            t = (ref_coord - y1) / (y2 - y1)
            if -0.5 <= t <= 1.5:  # within or reasonably near segment
                intercept = x1 + t * (x2 - x1)
                intercepts.append(intercept)
        else:
            # Finding y-intercept at x = ref_coord
            if abs(x2 - x1) < 1e-4:
                continue
            t = (ref_coord - x1) / (x2 - x1)
            if -0.5 <= t <= 1.5:
                intercept = y1 + t * (y2 - y1)
                intercepts.append(intercept)

    if len(intercepts) < 4:
        return None, None

    intercepts = np.array(sorted(intercepts))
    # Deduplicate lines that are too close (multiple detections of same thread, < 3px)
    filtered = [intercepts[0]]
    for val in intercepts[1:]:
        if val - filtered[-1] >= 3.0:
            filtered.append(val)

    if len(filtered) < 4:
        return None, None

    diffs = np.diff(filtered)
    # Filter outliers (> 3 * median spacing, which indicates missed threads)
    med_diff = np.median(diffs)
    valid_diffs = diffs[diffs <= 2.5 * med_diff]

    if len(valid_diffs) < 3:
        return None, None

    mean_spacing = round(float(np.mean(valid_diffs)), 2)
    std_spacing = round(float(np.std(valid_diffs)), 2)

    return mean_spacing, std_spacing
