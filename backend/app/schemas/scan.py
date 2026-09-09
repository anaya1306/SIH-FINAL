from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field

from app.schemas.field import ExtractedField
from app.schemas.violation import Violation


class ScanStatus(str, Enum):
    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"


class ScanCreate(BaseModel):
    product_name: str
    image_url: str | None = None
    raw_ocr_text: str | None = None


class ScanResponse(BaseModel):
    id: str
    status: ScanStatus
    product_name: str
    image_url: str | None = None
    created_at: datetime


class ScanDetailResponse(ScanResponse):
    compliance_score: int | None = None
    fields: list[ExtractedField] = Field(default_factory=list)
    violations: list[Violation] = Field(default_factory=list)


class ScanListResponse(BaseModel):
    items: list[ScanResponse]
    total: int
