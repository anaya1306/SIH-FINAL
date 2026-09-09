import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from rules_engine import validate_product

def test_complete_product():
    product = {
        "manufacturer": "Green Valley Foods Pvt.Ltd",
        "generic_name": "Basmati Rice",
        "net_quantity": "1 kg",
        "mrp": "₹120.00",
        "manufacturing_date": "01/05/2024",
        "consumer_care_phone": "+9118001234567",
        "consumer_care_email": "care@greenvalleyfoods.com",
        "inclusive_of_all_taxes": True
    }

    result = validate_product(product)

    assert "overall_status" in result
    assert "passed" in result
    assert "potential_violations" in result
    assert "needs_review" in result


def test_missing_mrp():
    product = {
        "manufacturer": "Test Company",
        "generic_name": "Rice",
        "net_quantity": "1 kg",
        "mrp": None,
        "manufacturing_date": "01/05/2024",
        "consumer_care_phone": "1234567890",
        "consumer_care_email": "test@example.com"
    }

    result = validate_product(product)

    assert any(
        item["field"] == "mrp"
        for item in result["needs_review"]
    )


def test_missing_manufacturing_date():
    product = {
        "manufacturer": "Test Company",
        "generic_name": "Rice",
        "net_quantity": "1 kg",
        "mrp": "₹100",
        "manufacturing_date": None,
        "consumer_care_phone": "1234567890",
        "consumer_care_email": "test@example.com"
    }

    result = validate_product(product)

    assert any(
        item["field"] == "manufacturing_date"
        for item in result["needs_review"]
    )


def test_missing_generic_name():
    product = {
        "manufacturer": "Test Company",
        "generic_name": None,
        "net_quantity": "1 kg",
        "mrp": "₹100",
        "manufacturing_date": "01/05/2024",
        "consumer_care_phone": "1234567890",
        "consumer_care_email": "test@example.com"
    }

    result = validate_product(product)

    assert any(
        item["field"] == "generic_name"
        for item in result["needs_review"]
    )


def test_missing_quantity():
    product = {
        "manufacturer": "Test Company",
        "generic_name": "Rice",
        "net_quantity": None,
        "mrp": "₹100",
        "manufacturing_date": "01/05/2024",
        "consumer_care_phone": "1234567890",
        "consumer_care_email": "test@example.com"
    }

    result = validate_product(product)

    assert any(
        item["field"] == "net_quantity"
        for item in result["needs_review"]
    )