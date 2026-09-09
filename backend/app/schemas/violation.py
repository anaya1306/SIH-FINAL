from enum import Enum

from pydantic import BaseModel, Field


class ViolationSeverity(str, Enum):
    critical = "critical"
    major = "major"
    minor = "minor"


class Violation(BaseModel):
    id: str
    scan_id: str
    rule_code: str
    severity: ViolationSeverity
    description: str
    expected: str
    actual: str
    field_name: str


class ViolationListResponse(BaseModel):
    items: list[Violation]
    total: int
    scan_id: str | None = None
