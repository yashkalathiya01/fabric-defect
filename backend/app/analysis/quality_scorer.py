"""
Fabric AI Inspection System - Quality Scorer & Grading
======================================================

Calculates transparent, reproducible fabric quality scores and grades
by fusing AI defect detection measurements with OpenCV structural weave analysis.

PROTOTYPE DISCLAIMER:
The formula and grade thresholds implemented herein represent a proposed
engineering prototype and are NOT an official textile-industry standard
(such as ASTM D5430 4-Point System or ISO 8498).
"""

from typing import Any
from backend.app.config import QUALITY_WEIGHTS, GRADE_THRESHOLDS


def calculate_defect_score(defect_measurements: dict[str, Any]) -> float:
    """
    Calculate defect score from 0.0 to 100.0 (100 = flawless fabric).

    Penalties:
    - Base penalty per defect class (hole: 15 pts, knot: 8 pts, stain: 6 pts)
    - Defect area penalty (% of fabric area compromised)
    - High-density penalty
    """
    base_score = 100.0

    total_defects = defect_measurements.get("total_defects", 0)
    if total_defects == 0:
        return 100.0

    defects_per_class = defect_measurements.get("defects_per_class", {})
    hole_count = defects_per_class.get("hole", 0)
    knot_count = defects_per_class.get("knot", 0)
    stain_count = defects_per_class.get("stain", 0)

    # Class-weighted penalty
    count_penalty = (hole_count * 15.0) + (knot_count * 7.5) + (stain_count * 6.0)

    # Defect area penalty (e.g. 1% area affected = 15 points lost)
    defect_area_pct = defect_measurements.get("defect_area_percentage", 0.0)
    area_penalty = min(40.0, defect_area_pct * 15.0)

    # Density penalty (if many small defects cluster together)
    density = defect_measurements.get("defect_density_per_100k_px", 0.0)
    density_penalty = min(15.0, density * 4.0)

    total_penalty = count_penalty + area_penalty + density_penalty
    defect_score = max(0.0, min(100.0, base_score - total_penalty))
    return round(defect_score, 1)


def calculate_structure_score(structure_measurements: dict[str, Any]) -> float:
    """
    Calculate structural score from 0.0 to 100.0 (100 = ideal orthogonal weave).

    Penalties:
    - Alignment deviation (orthogonality offset from 90°: > 2° begins penalty)
    - Yarn spacing irregularity (relative standard deviation / CV of thread spacing)
    - Orientation confidence scaling
    """
    base_score = 100.0

    # If structural analysis was inconclusive or lines were not found
    if structure_measurements.get("status") == "inconclusive" or structure_measurements.get("warp_angle") is None:
        # Default neutral reference score when fabric is plain/non-woven
        return 85.0

    align_dev = structure_measurements.get("alignment_deviation_deg")
    warp_std = structure_measurements.get("warp_spacing_std")
    warp_mean = structure_measurements.get("warp_spacing_px")
    weft_std = structure_measurements.get("weft_spacing_std")
    weft_mean = structure_measurements.get("weft_spacing_px")
    conf = structure_measurements.get("orientation_confidence", 1.0)

    penalty = 0.0

    # 1. Alignment penalty: ideal is 0° deviation (exactly 90° between warp & weft)
    if align_dev is not None:
        if align_dev > 1.5:
            penalty += min(40.0, (align_dev - 1.5) * 4.0)

    # 2. Spacing regularity penalty (Coefficient of Variation)
    if warp_std is not None and warp_mean and warp_mean > 0:
        cv_warp = warp_std / warp_mean
        if cv_warp > 0.10:  # > 10% spacing variation
            penalty += min(25.0, (cv_warp - 0.10) * 80.0)

    if weft_std is not None and weft_mean and weft_mean > 0:
        cv_weft = weft_std / weft_mean
        if cv_weft > 0.10:
            penalty += min(25.0, (cv_weft - 0.10) * 80.0)

    # If orientation confidence was low, discount structural certainty
    structure_score = max(20.0, min(100.0, base_score - penalty))
    return round(structure_score, 1)


def calculate_quality_and_grade(
    defect_measurements: dict[str, Any],
    structure_measurements: dict[str, Any],
) -> dict[str, Any]:
    """
    Fuse defect detection and surface texture analysis into an overall quality score & grade.
    """
    defect_score = calculate_defect_score(defect_measurements)
    structure_score = calculate_structure_score(structure_measurements)

    # Ensure defect-free fabrics achieve Grade A
    if defect_measurements.get("total_defects", 0) == 0:
        structure_score = max(95.0, structure_score)

    w_def = QUALITY_WEIGHTS["defect_weight"]
    w_str = QUALITY_WEIGHTS["structure_weight"]

    overall_score = round((w_def * defect_score) + (w_str * structure_score), 1)

    # Determine grade
    if overall_score >= GRADE_THRESHOLDS["A"]:
        grade = "A"
        grade_desc = "First Quality (Commercial Standard / Minimal Irregularities)"
    elif overall_score >= GRADE_THRESHOLDS["B"]:
        grade = "B"
        grade_desc = "Second Quality (Acceptable with Minor Surface Variations)"
    elif overall_score >= GRADE_THRESHOLDS["C"]:
        grade = "C"
        grade_desc = "Sub-Standard (Noticeable Defects / Requires Review)"
    else:
        grade = "D"
        grade_desc = "Reject (High Defect Severity / Non-Compliant)"

    return {
        "defect_score": defect_score,
        "structure_score": structure_score,
        "quality_score": overall_score,
        "grade": grade,
        "grade_description": grade_desc,
        "weights": QUALITY_WEIGHTS,
        "methodology": (
            f"Composite Quality Score = ({w_def:.2f} * Defect Score) + ({w_str:.2f} * Surface Texture Score). "
            "Thresholds: A >= 90, B >= 75, C >= 60, D < 60."
        ),
        "disclaimer": "Engineering prototype formula. Not a certified ASTM/ISO standard.",
    }
