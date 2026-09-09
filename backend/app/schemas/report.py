from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field

from app.schemas.field import ExtractedField
from app.schemas.violation import Violation


class ReportStatus(str, Enum):
    pass_ = "pass"
    fail = "fail"
    review = "review"


class ReportSummary(BaseModel):
    id: str
    scan_id: str
    product_name: str
    compliance_score: int
    violation_count: int
    status: ReportStatus
    generated_at: datetime


class ReportDetail(ReportSummary):
    fields: list[ExtractedField] = Field(default_factory=list)
    violations: list[Violation] = Field(default_factory=list)
    inspector_notes: str = ""
    recommendations: list[str] = Field(default_factory=list)


class ReportListResponse(BaseModel):
    items: list[ReportSummary]
    total: int
