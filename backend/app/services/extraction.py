import re
from datetime import datetime, timezone

from app.schemas.field import ExtractedField
from app.schemas.violation import Violation, ViolationSeverity


def _find(pattern: str, text: str, flags: int = re.IGNORECASE) -> re.Match[str] | None:
    return re.search(pattern, text, flags)


def extract_fields_from_text(raw_ocr_text: str) -> list[ExtractedField]:
    text = raw_ocr_text.strip()
    fields: list[ExtractedField] = []

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if lines:
        fields.append(
            ExtractedField(
                field_name="product_name",
                value=lines[0],
                confidence=0.94,
                source_text=lines[0],
            )
        )

    mrp_match = _find(r"MRP\s*(?:Rs\.?|₹)\s*([\d,]+(?:\.\d{1,2})?)", text)
    if mrp_match:
        fields.append(
            ExtractedField(
                field_name="mrp",
                value=mrp_match.group(1).replace(",", ""),
                confidence=0.97,
                source_text=mrp_match.group(0),
            )
        )

    qty_match = _find(
        r"(?:Net\s*(?:Quantity|Wt\.?|Weight)|Net\s*Wt\.?)\s*:?\s*([\d.]+\s*(?:ml|g|kg|L|l|gm|grams?))",
        text,
    )
    if qty_match:
        fields.append(
            ExtractedField(
                field_name="net_quantity",
                value=qty_match.group(1).strip(),
                confidence=0.96,
                source_text=qty_match.group(0),
            )
        )

    mfg_match = _find(r"Manufacturer\s*:\s*(.+?)(?:\n|Mfg|$)", text)
    if mfg_match:
        value = mfg_match.group(1).strip()
        fields.append(
            ExtractedField(
                field_name="manufacturer",
                value=value,
                confidence=0.91,
                source_text=f"Manufacturer: {value[:30]}..." if len(value) > 30 else f"Manufacturer: {value}",
            )
        )

    mfg_date_match = _find(r"Mfg\s*Date\s*:\s*([\d/\-]+)", text)
    if mfg_date_match:
        fields.append(
            ExtractedField(
                field_name="mfg_date",
                value=mfg_date_match.group(1),
                confidence=0.88,
                source_text=mfg_date_match.group(0),
            )
        )

    exp_match = _find(r"(?:Best\s*Before|Exp(?:iry)?(?:\s*Date)?)\s*:?\s*([\d/\-]+)", text)
    if exp_match:
        fields.append(
            ExtractedField(
                field_name="exp_date",
                value=exp_match.group(1),
                confidence=0.88,
                source_text=exp_match.group(0),
            )
        )

    return fields


def check_violations(scan_id: str, fields: list[ExtractedField], raw_text: str) -> list[Violation]:
    field_map = {f.field_name: f for f in fields}
    violations: list[Violation] = []
    counter = 1

    def add_violation(
        rule_code: str,
        severity: ViolationSeverity,
        description: str,
        expected: str,
        actual: str,
        field_name: str,
    ) -> None:
        nonlocal counter
        violations.append(
            Violation(
                id=f"vio-{scan_id.split('-')[-1]}-{counter:03d}",
                scan_id=scan_id,
                rule_code=rule_code,
                severity=severity,
                description=description,
                expected=expected,
                actual=actual,
                field_name=field_name,
            )
        )
        counter += 1

    if "mrp" not in field_map:
        add_violation(
            "LM-001",
            ViolationSeverity.critical,
            "MRP not found on label",
            "Maximum Retail Price with 'MRP' prefix",
            "Not detected",
            "mrp",
        )

    if "net_quantity" not in field_map:
        add_violation(
            "LM-002",
            ViolationSeverity.major,
            "Net quantity not declared",
            "Net quantity with unit (g/ml/kg/L)",
            "Not detected",
            "net_quantity",
        )

    if "manufacturer" not in field_map:
        add_violation(
            "LM-003",
            ViolationSeverity.major,
            "Manufacturer name not found",
            "Manufacturer or marketer name",
            "Not detected",
            "manufacturer",
        )

    if "manufacturer" in field_map and not re.search(
        r"\d{6}|\broad\b|\bstreet\b|\bnagar\b|\bdist\b|\bpin\b", raw_text, re.IGNORECASE
    ):
        add_violation(
            "LM-004",
            ViolationSeverity.major,
            "Manufacturer address not found on label",
            "Full manufacturer name and address",
            "Not detected",
            "manufacturer_address",
        )

    if not re.search(r"country\s+of\s+origin|made\s+in\s+india", raw_text, re.IGNORECASE):
        add_violation(
            "LM-007",
            ViolationSeverity.minor,
            "Country of origin not declared",
            "Country of origin statement",
            "Not detected",
            "country_of_origin",
        )

    return violations


def compute_compliance_score(violations: list[Violation]) -> int:
    if not violations:
        return 95
    score = 100
    for v in violations:
        if v.severity == ViolationSeverity.critical:
            score -= 25
        elif v.severity == ViolationSeverity.major:
            score -= 15
        else:
            score -= 5
    return max(0, min(100, score))


def utc_now() -> datetime:
    return datetime.now(timezone.utc)
