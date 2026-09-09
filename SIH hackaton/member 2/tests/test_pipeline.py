import json
import sys
from pathlib import Path

MEMBER2_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(MEMBER2_DIR))

from extractor import extract_fields
from rules_engine import validate_product


PROJECT_ROOT = Path(__file__).resolve().parents[2]
OCR_FILE = PROJECT_ROOT / "member1_ocr" / "ocr_output.json"


def test_real_ocr_pipeline():

    assert OCR_FILE.exists(), f"OCR file not found: {OCR_FILE}"

    with open(OCR_FILE, "r", encoding="utf-8") as file:
        ocr_data = json.load(file)

    product = extract_fields(ocr_data)

    compliance = validate_product(product)

    assert isinstance(product, dict)
    assert isinstance(compliance, dict)

    assert "overall_status" in compliance
    assert "passed" in compliance
    assert "potential_violations" in compliance
    assert "needs_review" in compliance

    required_product_keys = {
        "product_name",
        "generic_name",
        "net_quantity",
        "mrp",
        "manufacturer",
        "address",
        "batch_number",
        "manufacturing_date",
        "use_by_date",
        "consumer_care_phone",
        "consumer_care_email",
        "inclusive_of_all_taxes",
        "evidence"
    }

    assert required_product_keys.issubset(product)
    assert isinstance(product["evidence"], dict)