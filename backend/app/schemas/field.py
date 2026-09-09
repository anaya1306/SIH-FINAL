from datetime import datetime

from pydantic import BaseModel, Field


class ExtractedField(BaseModel):
    field_name: str
    value: str
    confidence: float = Field(ge=0.0, le=1.0)
    source_text: str


class ExtractRequest(BaseModel):
    raw_ocr_text: str


class ExtractResponse(BaseModel):
    scan_id: str
    fields: list[ExtractedField]
    extracted_at: datetime
