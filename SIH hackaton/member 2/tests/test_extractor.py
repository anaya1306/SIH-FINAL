import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from extractor import extract_fields

def test_basmati_extraction():

    ocr_data = {
        "regions": [
            {
                "text": "Nature's",
                "bbox": {"x": 182, "y": 36, "width": 114, "height": 26},
                "confidence": 0.98
            },
            {
                "text": "Goodness",
                "bbox": {"x": 173, "y": 63, "width": 128, "height": 27},
                "confidence": 0.99
            },
            {
                "text": "PREMIUM BASMATI RICE",
                "bbox": {"x": 98, "y": 109, "width": 261, "height": 21},
                "confidence": 0.95
            },
            {
                "text": "Manufactured &Packed by:",
                "bbox": {"x": 245, "y": 149, "width": 151, "height": 18},
                "confidence": 0.96
            },
            {
                "text": "Green Valley Foods Pvt.Ltd",
                "bbox": {"x": 248, "y": 174, "width": 147, "height": 13},
                "confidence": 0.96
            },
            {
                "text": "Net Quantity:1 kg",
                "bbox": {"x": 55, "y": 183, "width": 98, "height": 17},
                "confidence": 0.92
            },
            {
                "text": "MRPIncl.of all taxes):120.00",
                "bbox": {"x": 55, "y": 215, "width": 167, "height": 13},
                "confidence": 0.93
            },
            {
                "text": "Batch No.:BR240501",
                "bbox": {"x": 54, "y": 245, "width": 128, "height": 16},
                "confidence": 0.93
            },
            {
                "text": "MFD.:",
                "bbox": {"x": 54, "y": 279, "width": 36, "height": 18},
                "confidence": 0.91
            },
            {
                "text": "01/05/2024",
                "bbox": {"x": 112, "y": 279, "width": 75, "height": 17},
                "confidence": 0.99
            },
            {
                "text": "USE BY:30/04/2026",
                "bbox": {"x": 54, "y": 312, "width": 134, "height": 17},
                "confidence": 0.95
            },
            {
                "text": "Ph.+9118001234567",
                "bbox": {"x": 54, "y": 435, "width": 129, "height": 14},
                "confidence": 0.98
            },
            {
                "text": "Email:care@greenvalleyfoods.com",
                "bbox": {"x": 53, "y": 457, "width": 197, "height": 17},
                "confidence": 0.99
            }
        ]
    }

    result = extract_fields(ocr_data)

    assert result["product_name"] == "Nature's Goodness"
    assert result["generic_name"] == "Basmati Rice"
    assert result["net_quantity"] == "1 kg"
    assert result["mrp"] == "₹120.00"
    assert result["manufacturer"] == "Green Valley Foods Pvt.Ltd"
    assert result["batch_number"] == "BR240501"
    assert result["manufacturing_date"] == "01/05/2024"
    assert result["use_by_date"] == "30/04/2026"
    assert result["consumer_care_phone"] == "+9118001234567"
    assert result["consumer_care_email"] == "care@greenvalleyfoods.com"
    assert result["inclusive_of_all_taxes"] is True


def test_evidence_exists():

    ocr_data = {
        "regions": [
            {
                "text": "Net Quantity:1 kg",
                "bbox": {"x": 10, "y": 10, "width": 100, "height": 20},
                "confidence": 0.95
            }
        ]
    }

    result = extract_fields(ocr_data)

    assert "evidence" in result
    assert "net_quantity" in result["evidence"]
    assert result["evidence"]["net_quantity"]["regions"]


def test_manufacturer_address_follows_same_column_block():

    ocr_data = {
        "regions": [
            {
                "text": "Manufactured by:",
                "bbox": {"x": 205, "y": 10, "width": 120, "height": 16},
                "confidence": 0.96
            },
            {
                "text": "Example Foods Pvt Ltd",
                "bbox": {"x": 208, "y": 30, "width": 130, "height": 14},
                "confidence": 0.96
            },
            {
                "text": "Net Quantity:1 kg",
                "bbox": {"x": 20, "y": 48, "width": 100, "height": 16},
                "confidence": 0.96
            },
            {
                "text": "Plot 12, Industrial Area",
                "bbox": {"x": 208, "y": 50, "width": 130, "height": 14},
                "confidence": 0.96
            },
            {
                "text": "MRP:120",
                "bbox": {"x": 20, "y": 68, "width": 80, "height": 16},
                "confidence": 0.96
            },
            {
                "text": "Pune - 411001",
                "bbox": {"x": 208, "y": 70, "width": 100, "height": 14},
                "confidence": 0.96
            },
            {
                "text": "Notes",
                "bbox": {"x": 208, "y": 90, "width": 100, "height": 14},
                "confidence": 0.96
            },
            {
                "text": "Later address text",
                "bbox": {"x": 208, "y": 110, "width": 120, "height": 14},
                "confidence": 0.96
            }
        ]
    }

    result = extract_fields(ocr_data)

    assert result["address"] == "Plot 12, Industrial Area Pune - 411001"


def test_generic_name_ignores_organization_logo_region():

    ocr_data = {
        "regions": [
            {
                "text": "Harvest",
                "bbox": {"x": 220, "y": 20, "width": 100, "height": 24},
                "confidence": 0.98
            },
            {
                "text": "Spices",
                "bbox": {"x": 220, "y": 55, "width": 100, "height": 20},
                "confidence": 0.98
            },
            {
                "text": "NORTHSTAR GROUP",
                "bbox": {"x": 220, "y": 100, "width": 120, "height": 14},
                "confidence": 0.96
            },
            {
                "text": "Manufactured by:",
                "bbox": {"x": 220, "y": 140, "width": 120, "height": 14},
                "confidence": 0.96
            },
            {
                "text": "NORTHSTAR SEASONINGS PVT LTD",
                "bbox": {"x": 220, "y": 160, "width": 150, "height": 14},
                "confidence": 0.96
            }
        ]
    }

    result = extract_fields(ocr_data)

    assert result["generic_name"] == "Spices"
    assert result["evidence"]["generic_name"]["regions"][0]["text"] == "Spices"


def test_horizontal_label_value_pairs_and_non_food_descriptor():

    ocr_data = {
        "regions": [
            {
                "text": "PureGlow",
                "bbox": {"x": 180, "y": 20, "width": 110, "height": 24},
                "confidence": 0.98
            },
            {
                "text": "SHAMPOO",
                "bbox": {"x": 180, "y": 52, "width": 110, "height": 20},
                "confidence": 0.98
            },
            {
                "text": "Net Content",
                "bbox": {"x": 30, "y": 120, "width": 100, "height": 16},
                "confidence": 0.96
            },
            {
                "text": "200 ml",
                "bbox": {"x": 145, "y": 120, "width": 70, "height": 16},
                "confidence": 0.96
            },
            {
                "text": "Batch No.",
                "bbox": {"x": 30, "y": 150, "width": 80, "height": 16},
                "confidence": 0.96
            },
            {
                "text": "BAR4L027",
                "bbox": {"x": 125, "y": 150, "width": 80, "height": 16},
                "confidence": 0.96
            },
            {
                "text": "Mfg.Date",
                "bbox": {"x": 30, "y": 180, "width": 80, "height": 16},
                "confidence": 0.96
            },
            {
                "text": "DEC2024",
                "bbox": {"x": 125, "y": 180, "width": 80, "height": 16},
                "confidence": 0.96
            },
            {
                "text": "Use Before",
                "bbox": {"x": 30, "y": 210, "width": 80, "height": 16},
                "confidence": 0.96
            },
            {
                "text": "NOW2026",
                "bbox": {"x": 125, "y": 210, "width": 80, "height": 16},
                "confidence": 0.96
            }
        ]
    }

    result = extract_fields(ocr_data)

    assert result["generic_name"] == "Shampoo"
    assert result["batch_number"] == "BAR4L027"
    assert result["manufacturing_date"] == "DEC2024"
    assert result["use_by_date"] == "NOW2026"
    assert result["evidence"]["batch_number"]["regions"][1]["text"] == "BAR4L027"
    assert result["evidence"]["manufacturing_date"]["regions"][1]["text"] == "DEC2024"
    assert result["evidence"]["use_by_date"]["regions"][1]["text"] == "NOW2026"