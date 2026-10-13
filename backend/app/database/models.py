"""
Fabric AI Inspection System - Database Models
==============================================

SQLAlchemy ORM models for persisting fabric inspection records.
Stores metadata, defect measurements, structural values, and report paths.
The 500 MB model weights are NEVER stored in the database.
"""

from datetime import datetime
from sqlalchemy import Column, String, Float, Integer, DateTime, JSON, Text
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class InspectionRecord(Base):
    __tablename__ = "fabric_inspections"

    id = Column(Integer, primary_key=True, autoincrement=True)
    inspection_id = Column(String(64), unique=True, index=True, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Image files
    image_filename = Column(String(255), nullable=False)
    original_image_path = Column(Text, nullable=False)
    annotated_image_path = Column(Text, nullable=True)

    # Defect metrics
    total_defects = Column(Integer, default=0)
    hole_count = Column(Integer, default=0)
    knot_count = Column(Integer, default=0)
    stain_count = Column(Integer, default=0)
    defect_area_pct = Column(Float, default=0.0)

    # Quality and grading
    defect_score = Column(Float, nullable=True)
    structure_score = Column(Float, nullable=True)
    quality_score = Column(Float, nullable=True)
    grade = Column(String(10), nullable=True)
    grade_description = Column(String(255), nullable=True)

    # Structural measurements
    warp_angle = Column(Float, nullable=True)
    weft_angle = Column(Float, nullable=True)
    warp_spacing = Column(Float, nullable=True)
    weft_spacing = Column(Float, nullable=True)
    alignment_deviation = Column(Float, nullable=True)
    orientation_confidence = Column(Float, nullable=True)

    # Performance
    inference_time_ms = Column(Float, nullable=True)
    total_inspection_time_ms = Column(Float, nullable=True)

    # Report path
    report_pdf_path = Column(Text, nullable=True)

    # Raw JSON payload for full fidelity reconstruction
    full_result_json = Column(JSON, nullable=True)

    def to_summary_dict(self):
        return {
            "inspection_id": self.inspection_id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "image_filename": self.image_filename,
            "total_defects": self.total_defects,
            "defect_counts": {
                "hole": self.hole_count,
                "knot": self.knot_count,
                "stain": self.stain_count,
            },
            "quality_score": self.quality_score,
            "grade": self.grade,
            "grade_description": self.grade_description,
            "warp_angle": self.warp_angle,
            "weft_angle": self.weft_angle,
            "alignment_deviation": self.alignment_deviation,
            "has_report": bool(self.report_pdf_path),
        }
