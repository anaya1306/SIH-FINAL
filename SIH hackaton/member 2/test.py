from extractor import extract_fields
from rules_engine import validate_product


ocr_text = """
en no. & | : ? !Mtutton) ee Preyrediony, oo <1, GALT, CUM, TURMERIC,

250g (3 med ae. I CASSIA, NUEMEG, CLOVE. CARAWAY, GREEN -
CARDAMOY as g BLACK PEPPER, ANISTAR & BAY LEAVES

Tim 149 Raviwar Path, Pune- 411002 (India)

Te: @89-24478792/ +91-7248665544

Gme.® bamerservice@mckynasale.com

BatchNo:
USEBY:

MRP.: 15.00

(Inclusive of all taxes)

Food Products
"""


# STEP 1: Extract fields
# STEP 1: Extract fields
extracted_data = extract_fields(ocr_text)

print("\n========== EXTRACTED DATA ==========\n")

for field, value in extracted_data.items():
    print(f"{field:<25}: {value}")


# STEP 2: Validate extracted data
compliance_result = validate_product(extracted_data)

print("\n========== COMPLIANCE RESULT ==========\n")

print(f"Overall Status: {compliance_result['overall_status']}")


# STEP 4: Show potential violations
print("\n--- POTENTIAL VIOLATIONS ---")

for item in compliance_result["violations"]:
    print(
        f"Rule {item['rule_id']:<10} | "
        f"{item['field']:<20} | "
        f"{item['status']:<15} | "
        f"{item['issue']}"
    )