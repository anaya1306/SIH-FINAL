import json
import os
import re


def load_rules():
    """
    Load Legal Metrology rules from rules.json.
    """

    rules_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "rules.json"
    )

    with open(rules_path, "r", encoding="utf-8") as file:
        return json.load(file)


def is_present(value):
    """
    Check whether a field contains useful data.
    """

    if value is None:
        return False

    if isinstance(value, str):
        return value.strip() != ""

    if isinstance(value, dict):
        return any(
            v is not None and str(v).strip() != ""
            for v in value.values()
        )

    if isinstance(value, list):
        return len(value) > 0

    return True


def get_consumer_care_status(product):
    """
    Consumer care is considered detected if either
    telephone or email is available.
    """

    phone = product.get("consumer_care_phone")
    email = product.get("consumer_care_email")

    return is_present(phone) or is_present(email)


def validate_net_quantity_unit(value):
    """
    Basic OCR-level validation of quantity units.

    This checks whether the declared quantity appears
    to contain a recognizable unit.

    It does NOT verify actual physical quantity.
    """

    if not is_present(value):
        return False

    text = str(value).lower().strip()

    valid_units = [
        "g",
        "kg",
        "mg",
        "ml",
        "l",
        "litre",
        "liter",
        "litres",
        "liters",
        "cm",
        "m",
        "mm",
        "nos",
        "no",
        "number"
    ]

    pattern = r"\b(" + "|".join(
        re.escape(unit) for unit in valid_units
    ) + r")\b"

    return re.search(pattern, text) is not None


def validate_mrp(value):
    """
    Basic OCR-level MRP validation.

    Checks whether an MRP value contains a price-like number.

    It does NOT verify whether the printed price is legally
    correct compared with any external database.
    """

    if not is_present(value):
        return False

    text = str(value)

    return re.search(
        r"(?:₹|rs\.?|inr)?\s*\d+(?:\.\d{1,2})?",
        text,
        re.IGNORECASE
    ) is not None


def validate_manufacturing_date(value):
    """
    Basic OCR-level validation for month/year-style
    manufacturing declarations.

    Examples:
        08/2026
        08-2026
        08/26
        Aug 2026
        MFD: 08/2026
    """

    if not is_present(value):
        return False

    text = str(value).strip()

    patterns = [
        r"\b(0?[1-9]|1[0-2])[/\-]\d{2,4}\b",
        r"\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+\d{2,4}\b"
    ]

    for pattern in patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return True

    return False


def add_result(results, rule, status, issue=None):
    """
    Add a standardized rule result.
    """

    item = {
        "rule_id": rule["rule_id"],
        "field": rule["field"],
        "status": status,
        "description": rule["description"]
    }

    if issue:
        item["issue"] = issue

    results.append(item)


def validate_product(product):
    """
    Main Legal Metrology compliance validation engine.

    Output:
        passed
        potential_violations
        needs_review
        overall_status
    """

    rules = load_rules()

    passed = []
    potential_violations = []
    needs_review = []

    for rule in rules:

        rule_id = rule["rule_id"]
        field = rule["field"]
        check = rule.get("check", "required")
        description = rule["description"]

        # --------------------------------------------------
        # REQUIRED FIELD
        # --------------------------------------------------

        if check == "required":

            if field == "consumer_care":
                found = get_consumer_care_status(product)
            else:
                found = is_present(product.get(field))

            if found:
                add_result(
                    passed,
                    rule,
                    "FOUND"
                )
            else:
                add_result(
                    needs_review,
                    rule,
                    "NEEDS_REVIEW",
                    description + " not detected by OCR"
                )

        # --------------------------------------------------
        # RECOMMENDED FIELD
        # --------------------------------------------------

        elif check == "recommended":

            found = is_present(product.get(field))

            if found:
                add_result(
                    passed,
                    rule,
                    "FOUND"
                )
            else:
                add_result(
                    needs_review,
                    rule,
                    "OPTIONAL_REVIEW",
                    description + " not detected by OCR"
                )

        # --------------------------------------------------
        # UNIT CHECK
        # --------------------------------------------------

        elif check == "unit":

            value = product.get(field)

            if not is_present(value):
                add_result(
                    needs_review,
                    rule,
                    "NEEDS_REVIEW",
                    "Net quantity not detected by OCR"
                )

            elif validate_net_quantity_unit(value):
                add_result(
                    passed,
                    rule,
                    "VALID"
                )

            else:
                add_result(
                    potential_violations,
                    rule,
                    "POTENTIAL_VIOLATION",
                    "Net quantity unit could not be validated"
                )

        # --------------------------------------------------
        # MANUAL REVIEW
        # --------------------------------------------------

        elif check == "manual_review":

            add_result(
                needs_review,
                rule,
                "MANUAL_REVIEW",
                description
            )

    # ------------------------------------------------------
    # ADDITIONAL VALUE VALIDATIONS
    # ------------------------------------------------------

    # Manufacturing date format
    manufacturing_date = product.get("manufacturing_date")

    if is_present(manufacturing_date):

        if validate_manufacturing_date(manufacturing_date):

            passed.append({
                "rule_id": "6(1)(d)",
                "field": "manufacturing_date",
                "status": "VALID_FORMAT",
                "description": "Manufacturing date format detected"
            })

        else:

            potential_violations.append({
                "rule_id": "6(1)(d)",
                "field": "manufacturing_date",
                "status": "POTENTIAL_VIOLATION",
                "issue": "Manufacturing date detected but format could not be validated"
            })

    # MRP format
    mrp = product.get("mrp")

    if is_present(mrp):

        if validate_mrp(mrp):

            passed.append({
                "rule_id": "6(1)(e)",
                "field": "mrp",
                "status": "VALID_FORMAT",
                "description": "MRP value detected"
            })

        else:

            potential_violations.append({
                "rule_id": "6(1)(e)",
                "field": "mrp",
                "status": "POTENTIAL_VIOLATION",
                "issue": "MRP detected but price format could not be validated"
            })

    # ------------------------------------------------------
    # OVERALL STATUS
    # ------------------------------------------------------

    if potential_violations:
        overall_status = "POTENTIAL_VIOLATION"

    elif needs_review:
        overall_status = "NEEDS_REVIEW"

    else:
        overall_status = "POTENTIALLY_COMPLIANT"

    return {
        "overall_status": overall_status,
        "passed": passed,
        "potential_violations": potential_violations,
        "needs_review": needs_review
    }