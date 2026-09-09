import json
import os

from extractor import extract_fields
from rules_engine import validate_product


# =========================================================
# PATHS
# =========================================================

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

OCR_FILE = os.path.join(
    PROJECT_ROOT,
    "member1_ocr",
    "ocr_output.json"
)

OUTPUT_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "final_output.json"
)


# =========================================================
# LOAD OCR DATA
# =========================================================

with open(OCR_FILE, "r", encoding="utf-8") as file:
    ocr_data = json.load(file)


ocr_text = ocr_data.get("full_text", "")


# =========================================================
# RAW OCR
# =========================================================

print("\n========== RAW OCR TEXT ==========\n")
print(ocr_text)


# =========================================================
# FIELD EXTRACTION
# =========================================================

extracted_data = extract_fields(ocr_data)

print("\n========== EXTRACTED FIELDS ==========\n")

for field, value in extracted_data.items():

    if field != "evidence":
        print(f"{field:<25}: {value}")


# =========================================================
# EVIDENCE
# =========================================================

evidence = extracted_data.get("evidence", {})

print("\n========== EVIDENCE ==========\n")

for field, item in evidence.items():

    print(f"\n[{field}]")

    print(
        f"Value       : {item.get('value')}"
    )

    print(
        f"Source text : {item.get('source_text')}"
    )

    regions = item.get("regions", [])

    print(
        f"Regions     : {len(regions)}"
    )

    for region in regions:

        print(
            f"  - bbox={region.get('bbox')} "
            f"| confidence={region.get('confidence')}"
        )


# =========================================================
# COMPLIANCE
# =========================================================

compliance_result = validate_product(
    extracted_data
)

print("\n========== COMPLIANCE RESULT ==========\n")

print(
    "Overall Status:",
    compliance_result["overall_status"]
)


# =========================================================
# PASSED
# =========================================================

print("\n--- PASSED RULES ---")

for item in compliance_result["passed"]:

    print(
        f"Rule {item['rule_id']:<10} | "
        f"{item['field']:<20} | "
        f"{item['status']:<20} | "
        f"{item.get('description', '')}"
    )


# =========================================================
# POTENTIAL VIOLATIONS
# =========================================================

print("\n--- POTENTIAL VIOLATIONS ---")

for item in compliance_result["potential_violations"]:

    print(
        f"Rule {item['rule_id']:<10} | "
        f"{item['field']:<20} | "
        f"{item['status']:<20} | "
        f"{item.get('issue', item.get('description', ''))}"
    )


# =========================================================
# NEEDS REVIEW
# =========================================================

print("\n--- NEEDS REVIEW ---")

for item in compliance_result["needs_review"]:

    print(
        f"Rule {item['rule_id']:<10} | "
        f"{item['field']:<20} | "
        f"{item['status']:<20} | "
        f"{item.get('issue', item.get('description', ''))}"
    )


# =========================================================
# FIELD STATUS
# =========================================================

field_names = [
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
    "inclusive_of_all_taxes"
]


field_status = {}

for field in field_names:

    value = extracted_data.get(field)

    if value is None or value == "":
        status = "NOT_DETECTED"
    elif field in evidence:
        status = "FOUND"
    else:
        status = "FOUND"

    field_status[field] = {
        "value": value,
        "status": status
    }


# =========================================================
# FINAL OUTPUT
# =========================================================

final_output = {

    # -----------------------------------------------------
    # PRODUCT INFORMATION
    # -----------------------------------------------------

    "product": {
        "product_name": extracted_data.get(
            "product_name"
        ),

        "generic_name": extracted_data.get(
            "generic_name"
        ),

        "net_quantity": extracted_data.get(
            "net_quantity"
        ),

        "mrp": extracted_data.get(
            "mrp"
        ),

        "manufacturer": extracted_data.get(
            "manufacturer"
        ),

        "address": extracted_data.get(
            "address"
        ),

        "batch_number": extracted_data.get(
            "batch_number"
        ),

        "manufacturing_date": extracted_data.get(
            "manufacturing_date"
        ),

        "use_by_date": extracted_data.get(
            "use_by_date"
        ),

        "consumer_care_phone": extracted_data.get(
            "consumer_care_phone"
        ),

        "consumer_care_email": extracted_data.get(
            "consumer_care_email"
        ),

        "inclusive_of_all_taxes": extracted_data.get(
            "inclusive_of_all_taxes"
        )
    },


    # -----------------------------------------------------
    # FIELD STATUS
    # -----------------------------------------------------

    "field_status": field_status,


    # -----------------------------------------------------
    # EVIDENCE
    # -----------------------------------------------------

    "evidence": evidence,


    # -----------------------------------------------------
    # COMPLIANCE
    # -----------------------------------------------------

    "compliance": compliance_result,


    # -----------------------------------------------------
    # OCR
    # -----------------------------------------------------

    "ocr": {
        "engine": ocr_data.get(
            "engine"
        ),

        "image_size": ocr_data.get(
            "image_size"
        ),

        "full_text": ocr_data.get(
            "full_text"
        ),

        "regions": ocr_data.get(
            "regions",
            []
        )
    }
}


# =========================================================
# SAVE FINAL JSON
# =========================================================

with open(
    OUTPUT_FILE,
    "w",
    encoding="utf-8"
) as file:

    json.dump(
        final_output,
        file,
        indent=2,
        ensure_ascii=False
    )


print("\n========================================")
print(
    f"Final output saved to: {OUTPUT_FILE}"
)
print("========================================")