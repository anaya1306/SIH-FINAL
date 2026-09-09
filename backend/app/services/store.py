from dataclasses import dataclass, field
from datetime import datetime, timezone

from app.schemas.field import ExtractedField
from app.schemas.report import ReportDetail, ReportStatus
from app.schemas.scan import ScanStatus
from app.schemas.violation import Violation
from app.services.extraction import compute_compliance_score


@dataclass
class ScanRecord:
    id: str
    status: ScanStatus
    product_name: str
    image_url: str | None
    raw_ocr_text: str | None
    created_at: datetime
    fields: list[ExtractedField] = field(default_factory=list)
    violations: list[Violation] = field(default_factory=list)
    compliance_score: int | None = None


@dataclass
class ReportRecord:
    id: str
    scan_id: str
    product_name: str
    compliance_score: int
    violation_count: int
    status: ReportStatus
    generated_at: datetime
    inspector_notes: str = ""
    recommendations: list[str] = field(default_factory=list)


class InMemoryStore:
    def __init__(self) -> None:
        self.scans: dict[str, ScanRecord] = {}
        self.reports: dict[str, ReportRecord] = {}
        self._scan_counter = 4
        self._report_counter = 2

    def next_scan_id(self) -> str:
        self._scan_counter += 1
        return f"scan-{self._scan_counter:03d}"

    def next_report_id(self) -> str:
        self._report_counter += 1
        return f"rpt-{self._report_counter:03d}"

    def get_scan(self, scan_id: str) -> ScanRecord | None:
        return self.scans.get(scan_id)

    def list_scans(self) -> list[ScanRecord]:
        return sorted(self.scans.values(), key=lambda s: s.created_at, reverse=True)

    def create_scan(
        self,
        product_name: str,
        image_url: str | None = None,
        raw_ocr_text: str | None = None,
        status: ScanStatus = ScanStatus.pending,
    ) -> ScanRecord:
        scan_id = self.next_scan_id()
        record = ScanRecord(
            id=scan_id,
            status=status,
            product_name=product_name,
            image_url=image_url,
            raw_ocr_text=raw_ocr_text,
            created_at=datetime.now(timezone.utc),
        )
        self.scans[scan_id] = record
        return record

    def update_scan_fields(
        self, scan_id: str, fields: list[ExtractedField], violations: list[Violation]
    ) -> ScanRecord:
        scan = self.scans[scan_id]
        scan.fields = fields
        scan.violations = violations
        scan.compliance_score = compute_compliance_score(violations)
        scan.status = ScanStatus.completed
        return scan

    def list_violations(self, scan_id: str | None = None) -> list[Violation]:
        if scan_id:
            scan = self.scans.get(scan_id)
            return scan.violations if scan else []
        result: list[Violation] = []
        for scan in self.scans.values():
            result.extend(scan.violations)
        return result

    def list_reports(self) -> list[ReportRecord]:
        return sorted(self.reports.values(), key=lambda r: r.generated_at, reverse=True)

    def get_report(self, report_id: str) -> ReportRecord | None:
        return self.reports.get(report_id)

    def generate_report(self, scan_id: str) -> ReportDetail:
        scan = self.scans[scan_id]
        status = ReportStatus.pass_ if not scan.violations else ReportStatus.fail
        recommendations = []
        if any(v.field_name == "manufacturer_address" for v in scan.violations):
            recommendations.append(
                "Ensure manufacturer name and registered address are printed on the principal display panel."
            )
        if any(v.field_name == "country_of_origin" for v in scan.violations):
            recommendations.append(
                "Add country of origin declaration per Legal Metrology (Packaged Commodities) Rules."
            )

        notes = (
            "Automated inspection — manual review recommended for manufacturer details."
            if scan.violations
            else "Automated inspection passed with no violations detected."
        )

        report_id = self.next_report_id()
        record = ReportRecord(
            id=report_id,
            scan_id=scan.id,
            product_name=scan.product_name,
            compliance_score=scan.compliance_score or 0,
            violation_count=len(scan.violations),
            status=status,
            generated_at=datetime.fromisoformat("2026-09-02T09:15:00+00:00"),
            inspector_notes=notes,
            recommendations=recommendations,
        )
        self.reports[report_id] = record

        return ReportDetail(
            id=record.id,
            scan_id=record.scan_id,
            product_name=record.product_name,
            compliance_score=record.compliance_score,
            violation_count=record.violation_count,
            status=record.status,
            generated_at=record.generated_at,
            fields=scan.fields,
            violations=scan.violations,
            inspector_notes=record.inspector_notes,
            recommendations=record.recommendations,
        )


store = InMemoryStore()
