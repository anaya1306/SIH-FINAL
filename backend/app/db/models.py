from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker

from app.config import settings


class Base(DeclarativeBase):
    pass


class ScanModel(Base):
    __tablename__ = "scans"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    product_name: Mapped[str] = mapped_column(String(255))
    image_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    raw_ocr_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    compliance_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    fields: Mapped[list["ExtractedFieldModel"]] = relationship(back_populates="scan")
    violations: Mapped[list["ViolationModel"]] = relationship(back_populates="scan")


class ExtractedFieldModel(Base):
    __tablename__ = "extracted_fields"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    scan_id: Mapped[str] = mapped_column(String(36), ForeignKey("scans.id"))
    field_name: Mapped[str] = mapped_column(String(64))
    value: Mapped[str] = mapped_column(String(512))
    confidence: Mapped[float] = mapped_column(Float)
    source_text: Mapped[str] = mapped_column(Text)

    scan: Mapped["ScanModel"] = relationship(back_populates="fields")


class ViolationModel(Base):
    __tablename__ = "violations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    scan_id: Mapped[str] = mapped_column(String(36), ForeignKey("scans.id"))
    rule_code: Mapped[str] = mapped_column(String(16))
    severity: Mapped[str] = mapped_column(String(16))
    description: Mapped[str] = mapped_column(Text)
    expected: Mapped[str] = mapped_column(Text)
    actual: Mapped[str] = mapped_column(Text)
    field_name: Mapped[str] = mapped_column(String(64))

    scan: Mapped["ScanModel"] = relationship(back_populates="violations")


class ReportModel(Base):
    __tablename__ = "reports"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    scan_id: Mapped[str] = mapped_column(String(36), ForeignKey("scans.id"))
    product_name: Mapped[str] = mapped_column(String(255))
    compliance_score: Mapped[int] = mapped_column(Integer)
    violation_count: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(16))
    inspector_notes: Mapped[str] = mapped_column(Text, default="")
    recommendations: Mapped[str] = mapped_column(Text, default="[]")
    generated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


engine = None
SessionLocal = None

if settings.database_url:
    engine = create_engine(settings.database_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
