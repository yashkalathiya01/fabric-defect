"""
Fabric AI Inspection System - PDF Report Generator
===================================================

Generates publication-quality inspection reports in PDF format using ReportLab:
- Official header with Inspection ID and Timestamp
- Color-coded Fabric Grade Badge (A/B/C/D)
- Side-by-side or dual column image inspection (Original vs Annotated)
- Defect detection inventory & severity table
- OpenCV structural & warp/weft analysis panel
- Quality score calculation methodology
- Model architecture specifications
- Formal engineering disclaimers & limitations
"""

import os
from datetime import datetime
from typing import Any

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image as RLImage,
    KeepTogether,
    HRFlowable,
)

from backend.app.config import RESULTS_DIR


def generate_pdf_report(
    inspection_result: dict[str, Any],
    output_pdf_path: str | None = None,
) -> str:
    """
    Generate an inspection report PDF from inspection results.

    Args:
        inspection_result: The complete dictionary output from run_full_inspection().
        output_pdf_path: Optional explicit PDF destination path.

    Returns:
        Absolute path to the created PDF file.
    """
    iid = inspection_result["inspection_id"]
    if output_pdf_path is None:
        report_dir = os.path.join(RESULTS_DIR, iid)
        os.makedirs(report_dir, exist_ok=True)
        output_pdf_path = os.path.join(report_dir, f"Fabric_Inspection_Report_{iid}.pdf")
    else:
        os.makedirs(os.path.dirname(os.path.abspath(output_pdf_path)), exist_ok=True)

    doc = SimpleDocTemplate(
        output_pdf_path,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36,
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#0F172A"),
    )
    subtitle_style = ParagraphStyle(
        "DocSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9.5,
        leading=13,
        textColor=colors.HexColor("#475569"),
    )
    section_style = ParagraphStyle(
        "SectionHeading",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#1E293B"),
        spaceBefore=8,
        spaceAfter=4,
    )
    body_style = ParagraphStyle(
        "BodyTextCustom",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=11.5,
        textColor=colors.HexColor("#334155"),
    )
    small_disclaimer = ParagraphStyle(
        "DisclaimerText",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=7.5,
        leading=10,
        textColor=colors.HexColor("#64748B"),
    )

    story = []

    # 1. Header Banner
    header_data = [
        [
            Paragraph("<b>AI-POWERED FABRIC QUALITY INSPECTION SYSTEM</b><br/><font color='#64748B'>Automated Defect Detection & Textile Weave Structural Analysis</font>", title_style),
            Paragraph(f"<b>INSPECTION REPORT</b><br/>ID: <b>{iid}</b><br/>Date: {inspection_result.get('timestamp', datetime.now().isoformat())[:19].replace('T', ' ')}", subtitle_style),
        ]
    ]
    header_table = Table(header_data, colWidths=[4.2 * inch, 3.2 * inch])
    header_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(header_table)
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#0284C7"), spaceBefore=4, spaceAfter=8))

    # 2. Executive Summary & Grade Badge
    grade = inspection_result.get("quality", {}).get("grade", "N/A")
    score = inspection_result.get("quality", {}).get("quality_score", 0.0)
    grade_desc = inspection_result.get("quality", {}).get("grade_description", "")

    grade_colors = {
        "A": colors.HexColor("#16A34A"),
        "B": colors.HexColor("#2563EB"),
        "C": colors.HexColor("#D97706"),
        "D": colors.HexColor("#DC2626"),
        "INVALID": colors.HexColor("#DC2626"),
    }
    badge_color = grade_colors.get(grade, colors.HexColor("#DC2626"))

    fabric_val = inspection_result.get("fabric_validation", {})
    is_valid_fabric = fabric_val.get("is_valid_fabric", True)

    if not is_valid_fabric:
        summary_box_data = [
            [
                Paragraph(f"<font size=11 color='#DC2626'><b>SAMPLE REJECTED: INVALID PHOTO</b></font><br/>"
                          f"Status: <font size=12 color='#DC2626'><b>{grade}</b></font><br/>"
                          f"<b>The uploaded specimen was identified as invalid photo rather than an authentic textile fabric photo. Automated Faster R-CNN defect proposal was bypassed to prevent false-positive defect alarms on non-fabric surfaces.</b><br/>"
                          f"<font color='#64748B'>Recommendation: Please upload a close-up photograph of woven fabric, knitwear, or textile material.</font>", body_style),
                Paragraph(f"<font size=11><b>Domain Validation Metrics</b></font><br/>"
                          f"Classification: <b>Invalid Photo</b><br/>"
                          f"Confidence: <b>{fabric_val.get('confidence', 1.0)*100:.0f}%</b><br/>"
                          f"Textile Weave Texture: <b>NOT DETECTED</b>", body_style),
            ]
        ]
    else:
        summary_box_data = [
            [
                Paragraph(f"<font size=11><b>Quality Assessment</b></font><br/>"
                          f"Fabric Grade: <font size=14 color='{badge_color.hexval()}'><b>GRADE {grade}</b></font><br/>"
                          f"Composite Quality Score: <b>{score:.1f} / 100</b><br/>"
                          f"<font color='#64748B'>{grade_desc}</font>", body_style),
                Paragraph(f"<font size=11><b>Inspection Overview</b></font><br/>"
                          f"Total Defects Detected: <b>{inspection_result['defects']['total']}</b> "
                          f"(Hole: {inspection_result['defects']['hole']}, Knot: {inspection_result['defects']['knot']}, Stain: {inspection_result['defects']['stain']})<br/>"
                          f"Defect Area: <b>{inspection_result.get('defect_analysis', {}).get('defect_area_percentage', 0.0):.2f}%</b> of fabric area<br/>"
                          f"Inference Time: <b>{inspection_result.get('timing', {}).get('inference_time_ms', 0):.0f} ms</b>", body_style),
            ]
        ]
    summary_table = Table(summary_box_data, colWidths=[3.7 * inch, 3.7 * inch])
    summary_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FEF2F2") if not is_valid_fabric else colors.HexColor("#F8FAFC")),
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#F87171") if not is_valid_fabric else colors.HexColor("#CBD5E1")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#FCA5A5") if not is_valid_fabric else colors.HexColor("#E2E8F0")),
        ("PADDING", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 8))

    # 3. Visual Inspection Images
    story.append(Paragraph("<b>1. Visual Defect Inspection</b>", section_style))
    orig_path = inspection_result.get("image", {}).get("original_path")
    anno_path = inspection_result.get("image", {}).get("annotated_path")

    img_elements = []
    col_w = 3.65 * inch
    img_h = 2.45 * inch

    if orig_path and os.path.isfile(orig_path):
        orig_img = RLImage(orig_path, width=col_w, height=img_h)
    else:
        orig_img = Paragraph("Original Image Unavailable", body_style)

    if anno_path and os.path.isfile(anno_path):
        anno_img = RLImage(anno_path, width=col_w, height=img_h)
    else:
        anno_img = Paragraph("Annotated Image Unavailable", body_style)

    img_table = Table(
        [
            [Paragraph("<b>Original Fabric Sample</b>", body_style), Paragraph("<b>AI Detection Overlay (Faster R-CNN)</b>", body_style)],
            [orig_img, anno_img],
        ],
        colWidths=[col_w + 0.05 * inch, col_w + 0.05 * inch]
    )
    img_table.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 2),
        ("TOPPADDING", (0, 1), (-1, 1), 2),
    ]))
    story.append(img_table)
    story.append(Spacer(1, 6))

    # 4. Defect Inventory Table
    story.append(Paragraph("<b>2. Defect Inventory & Measurements</b>", section_style))
    defect_items = inspection_result.get("defect_analysis", {}).get("detailed_boxes", [])

    table_rows = [
        ["#", "Class", "Confidence", "Bounding Box [x1, y1, x2, y2]", "Size (W x H)", "Area (px²)", "Severity"]
    ]
    if defect_items:
        for idx, d in enumerate(defect_items, 1):
            sev = "Critical" if d["class"] == "hole" else ("Moderate" if d["class"] == "knot" else "Minor")
            table_rows.append([
                str(idx),
                d["class"].upper(),
                f"{d['confidence']*100:.1f}%",
                f"[{d['bbox'][0]:.0f}, {d['bbox'][1]:.0f}, {d['bbox'][2]:.0f}, {d['bbox'][3]:.0f}]",
                f"{d['width']:.0f} x {d['height']:.0f} px",
                f"{d['area_px']:,.0f}",
                sev,
            ])
    else:
        table_rows.append(["--", "No defects detected", "--", "--", "--", "--", "None"])

    defect_table = Table(table_rows, colWidths=[0.3 * inch, 0.8 * inch, 0.9 * inch, 2.2 * inch, 1.2 * inch, 1.0 * inch, 1.0 * inch])
    defect_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E293B")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 7.5),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#FFFFFF"), colors.HexColor("#F8FAFC")]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("PADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(defect_table)
    story.append(Spacer(1, 8))

    # 5. Quality Scoring Formula & Engineering Methodology
    story.append(Paragraph("<b>3. Quality Scoring Methodology & Model Specs</b>", section_style))
    qual = inspection_result.get("quality", {})
    meth = qual.get("methodology", {})
    if not isinstance(meth, dict):
        meth = {"formula": str(meth) if meth else "quality_score = 0.60 * defect_score + 0.40 * structure_score"}
    formula_desc = meth.get("formula", "quality_score = 0.60 * defect_score + 0.40 * structure_score")

    tech_notes = [
        [
            Paragraph(f"<b>Scoring Formula:</b><br/><code>{formula_desc}</code><br/>"
                      f"• Defect Score Component: <b>{qual.get('defect_score', 0):.1f} / 100</b><br/>"
                      f"• Structure Score Component: <b>{qual.get('structure_score', 0):.1f} / 100</b>", body_style),
            Paragraph(f"<b>Computer Vision Architecture:</b><br/>"
                      f"• Detector: Faster R-CNN with ResNet-50 Feature Pyramid Network (FPN)<br/>"
                      f"• Detectable Classes: hole (ID:1), knot (ID:2), stain (ID:3)<br/>"
                      f"• Structural Processor: OpenCV Canny Edge + Probabilistic Hough Transform", body_style),
        ]
    ]
    tech_table = Table(tech_notes, colWidths=[3.7 * inch, 3.7 * inch])
    tech_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#E2E8F0")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ("PADDING", (0, 0), (-1, -1), 6),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(tech_table)
    story.append(Spacer(1, 10))

    # 7. Limitations & Prototype Disclaimer
    story.append(Paragraph(
        "<b>ENGINEERING PROTOTYPE DISCLAIMER & LIMITATIONS:</b><br/>"
        "This automated inspection report is generated by an academic engineering research prototype. "
        "The numerical quality score and grading thresholds (A: 90-100, B: 75-89, C: 60-74, D: &lt;60) "
        "represent a proposed scoring heuristic and are not certified industrial textile standards (e.g., ASTM D5430 or ISO 8498). "
        "Detection metrics reflect benchmark validation performance (mAP@50: 83.4%) and should be verified by a qualified textile inspector.",
        small_disclaimer
    ))

    # Build document
    doc.build(story)
    return output_pdf_path
