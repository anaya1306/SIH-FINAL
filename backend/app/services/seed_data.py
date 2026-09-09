from datetime import datetime, timezone

from app.schemas.field import ExtractedField
from app.schemas.report import ReportStatus
from app.schemas.scan import ScanStatus
from app.schemas.violation import Violation, ViolationSeverity
from app.services.store import InMemoryStore, ReportRecord, ScanRecord, store


def _dt(iso: str) -> datetime:
    return datetime.fromisoformat(iso.replace("Z", "+00:00"))


def seed_store() -> None:
    """Populate in-memory store with sample legal-metrology inspection data."""

    store.scans["scan-001"] = ScanRecord(
        id="scan-001",
        status=ScanStatus.completed,
        product_name="Amul Taaza Toned Milk",
        image_url="https://storage.example.com/scans/amul-milk.jpg",
        raw_ocr_text=(
            "Amul Taaza Toned Milk\n"
            "MRP Rs. 28.00 (incl. of all taxes)\n"
            "Net Quantity: 500 ml\n"
            "Manufacturer: Gujarat Cooperative Milk Marketing Federation\n"
            "Mfg Date: 15/08/2026\n"
            "Best Before: 14/09/2026\n"
            "Made in India"
        ),
        created_at=_dt("2026-09-02T08:30:00Z"),
        fields=[
            ExtractedField(field_name="product_name", value="Amul Taaza Toned Milk", confidence=0.94, source_text="Amul Taaza Toned Milk"),
            ExtractedField(field_name="mrp", value="28.00", confidence=0.97, source_text="MRP Rs. 28.00"),
            ExtractedField(field_name="net_quantity", value="500 ml", confidence=0.96, source_text="Net Quantity: 500 ml"),
            ExtractedField(field_name="manufacturer", value="Gujarat Cooperative Milk Marketing Federation", confidence=0.91, source_text="Manufacturer: Gujarat Cooperative..."),
            ExtractedField(field_name="mfg_date", value="15/08/2026", confidence=0.88, source_text="Mfg Date: 15/08/2026"),
            ExtractedField(field_name="exp_date", value="14/09/2026", confidence=0.88, source_text="Best Before: 14/09/2026"),
        ],
        violations=[],
        compliance_score=95,
    )

    store.scans["scan-002"] = ScanRecord(
        id="scan-002",
        status=ScanStatus.completed,
        product_name="Maggi 2-Minute Noodles",
        image_url="https://storage.example.com/scans/maggi-pack.jpg",
        raw_ocr_text="Maggi 2-Minute Noodles\nMRP ₹14\nNet Wt. 70g",
        created_at=_dt("2026-09-02T09:00:00Z"),
        fields=[
            ExtractedField(field_name="mrp", value="14.00", confidence=0.95, source_text="MRP ₹14"),
            ExtractedField(field_name="net_quantity", value="70g", confidence=0.93, source_text="Net Wt. 70g"),
        ],
        violations=[
            Violation(
                id="vio-003",
                scan_id="scan-002",
                rule_code="LM-004",
                severity=ViolationSeverity.major,
                description="Manufacturer address not found on label",
                expected="Full manufacturer name and address",
                actual="Not detected",
                field_name="manufacturer_address",
            ),
            Violation(
                id="vio-004",
                scan_id="scan-002",
                rule_code="LM-007",
                severity=ViolationSeverity.minor,
                description="Country of origin not declared",
                expected="Country of origin statement",
                actual="Not detected",
                field_name="country_of_origin",
            ),
        ],
        compliance_score=72,
    )

    store.scans["scan-003"] = ScanRecord(
        id="scan-003",
        status=ScanStatus.pending,
        product_name="Tata Salt 1kg",
        image_url="https://storage.example.com/scans/tata-salt.jpg",
        raw_ocr_text=None,
        created_at=_dt("2026-09-02T09:30:00Z"),
    )

    store.reports["rpt-001"] = ReportRecord(
        id="rpt-001",
        scan_id="scan-002",
        product_name="Maggi 2-Minute Noodles",
        compliance_score=72,
        violation_count=2,
        status=ReportStatus.fail,
        generated_at=_dt("2026-09-02T09:15:00Z"),
        inspector_notes="Automated inspection — manual review recommended for manufacturer details.",
        recommendations=[
            "Ensure manufacturer name and registered address are printed on the principal display panel.",
            "Add country of origin declaration per Legal Metrology (Packaged Commodities) Rules.",
        ],
    )

    store.reports["rpt-002"] = ReportRecord(
        id="rpt-002",
        scan_id="scan-001",
        product_name="Amul Taaza Toned Milk",
        compliance_score=95,
        violation_count=0,
        status=ReportStatus.pass_,
        generated_at=_dt("2026-09-02T08:45:00Z"),
        inspector_notes="Automated inspection passed with no violations detected.",
        recommendations=[],
    )

    store._scan_counter = 4
    store._report_counter = 2
