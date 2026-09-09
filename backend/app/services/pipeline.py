import json
from pathlib import Path
from typing import Any

from app.schemas.field import ExtractedField
from app.schemas.violation import Violation, ViolationSeverity
from app.services.extraction import compute_compliance_score
from app.services.ocr_client import call_ocr_api_sync


OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)
OCR_OUTPUT = OUTPUT_DIR / "ocr_output.json"
EXTRACTED_OUTPUT = OUTPUT_DIR / "extracted_output.json"


def _read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)


def _normalize_value(value: Any) -> str | None:
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        return "true" if value else None
    return str(value)


def _build_fields_from_extracted(extracted: dict[str, Any]) -> list[ExtractedField]:
    fields: list[ExtractedField] = []
    field_mapping = {
        "batch_number": "batch_number",
        "manufacturing_date": "manufacturing_date",
        "expiry_date": "use_by_date",
        "net_weight": "net_quantity",
        "mrp": "mrp",
        "company_name": "manufacturer",
        "product_name": "product_name",
        "fssai_license": "fssai_license",
        "ingredient_list": "ingredients",
    }

    for ocr_field, backend_field in field_mapping.items():
        value = extracted.get(ocr_field)
        normalized = _normalize_value(value)
        if normalized is None:
            continue
        fields.append(
            ExtractedField(
                field_name=backend_field,
                value=normalized,
                confidence=0.92,
                source_text=normalized,
            )
        )
    return fields


def _check_missing_fields(fields: list[ExtractedField], scan_id: str) -> list[Violation]:
    violations: list[Violation] = []
    field_map = {f.field_name: f for f in fields}
    counter = 1

    def add_violation(rule_code: str, severity: ViolationSeverity, description: str, field_name: str) -> None:
        nonlocal counter
        violations.append(
            Violation(
                id=f"vio-{scan_id.split('-')[-1]}-{counter:03d}",
                scan_id=scan_id,
                rule_code=rule_code,
                severity=severity,
                description=description,
                expected=description,
                actual="Not detected" if field_name not in field_map else field_map[field_name].value,
                field_name=field_name,
            )
        )
        counter += 1

    if "mrp" not in field_map:
        add_violation("LM-001", ViolationSeverity.critical, "MRP not found on label", "mrp")
    if "net_quantity" not in field_map:
        add_violation("LM-002", ViolationSeverity.major, "Net quantity not declared", "net_quantity")
    if "manufacturer" not in field_map:
        add_violation("LM-003", ViolationSeverity.major, "Manufacturer name not found", "manufacturer")
    if "batch_number" not in field_map:
        add_violation("LM-005", ViolationSeverity.major, "Batch number not found", "batch_number")
    if "manufacturing_date" not in field_map:
        add_violation("LM-006", ViolationSeverity.major, "Manufacturing date not found", "manufacturing_date")
    if "use_by_date" not in field_map:
        add_violation("LM-007", ViolationSeverity.major, "Expiry date not found", "use_by_date")

    return violations


def get_pipeline_analysis(
    product_name: str = "Demo Product",
    image_url: str | None = None,
    uploaded_image_path: str | None = None,
) -> dict[str, Any]:
    ocr_data = {}
    extracted = {}

    if uploaded_image_path:
        try:
            with open(uploaded_image_path, "rb") as f:
                image_bytes = f.read()
            print(f"[pipeline] Image size: {len(image_bytes)} bytes")
            ocr_data = call_ocr_api_sync(image_bytes, mode="citizen", engine="auto")
            print(f"[pipeline] OCR returned keys: {list(ocr_data.keys())}")
            extracted = ocr_data.get("extracted", {})
            print(f"[pipeline] Extracted: {extracted}")
            _write_json(OCR_OUTPUT, ocr_data)
            _write_json(EXTRACTED_OUTPUT, extracted)
        except Exception as e:
            import traceback
            traceback.print_exc()
            ocr_data = {"full_text": "", "engine": "error", "extracted": {}}
            extracted = {}

    fields = _build_fields_from_extracted(extracted)
    violations = _check_missing_fields(fields, scan_id="scan-000")

    return {
        "product_name": extracted.get("product_name") or product_name,
        "image_url": image_url,
        "raw_ocr_text": ocr_data.get("full_text", ""),
        "fields": fields,
        "violations": violations,
        "compliance_score": compute_compliance_score(violations) if violations else 95,
        "engine": ocr_data.get("engine"),
        "overall_status": "PASS" if not violations else "NEEDS_REVIEW",
    }
