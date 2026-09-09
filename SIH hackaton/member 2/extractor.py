import re


def normalize_text(text):
    """Clean spacing only. Never manually correct OCR text."""
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


def make_evidence(regions, value=None):
    """Create evidence while preserving raw OCR text."""
    if not isinstance(regions, list):
        regions = [regions]

    return {
        "value": value,
        "source_text": " ".join(
            region.get("text", "") for region in regions
        ).strip(),
        "regions": [
            {
                "text": region.get("text"),
                "bbox": region.get("bbox"),
                "confidence": region.get("confidence")
            }
            for region in regions
        ]
    }


def get_bbox(region):
    return region.get("bbox") or {}


def center_x(region):
    bbox = get_bbox(region)
    return bbox.get("x", 0) + bbox.get("width", 0) / 2


def center_y(region):
    bbox = get_bbox(region)
    return bbox.get("y", 0) + bbox.get("height", 0) / 2


def top_y(region):
    return get_bbox(region).get("y", 0)


def bottom_y(region):
    bbox = get_bbox(region)
    return bbox.get("y", 0) + bbox.get("height", 0)


def horizontal_overlap(region1, region2):
    """Return horizontal overlap between two OCR regions."""
    b1 = get_bbox(region1)
    b2 = get_bbox(region2)

    left1 = b1.get("x", 0)
    right1 = left1 + b1.get("width", 0)

    left2 = b2.get("x", 0)
    right2 = left2 + b2.get("width", 0)

    return max(0, min(right1, right2) - max(left1, left2))


def same_column(region1, region2, tolerance=120):
    """
    Layout-aware column check.

    Uses center distance instead of the previous very broad
    220px tolerance.
    """
    return abs(center_x(region1) - center_x(region2)) <= tolerance


def is_below(region1, region2, max_gap=80):
    return (
        top_y(region2) >= bottom_y(region1)
        and top_y(region2) - bottom_y(region1) <= max_gap
    )


def find_region_below(
    regions,
    index,
    max_gap=80,
    x_tolerance=120
):
    """
    Find nearest OCR region below a label while respecting
    the label's horizontal column.
    """

    source = regions[index]
    candidates = []

    for i, region in enumerate(regions):

        if i == index:
            continue

        if not same_column(source, region, x_tolerance):
            continue

        if not is_below(source, region, max_gap):
            continue

        distance = top_y(region) - bottom_y(source)

        candidates.append(
            (distance, i, region)
        )

    candidates.sort(key=lambda item: item[0])

    if candidates:
        return candidates[0][1], candidates[0][2]

    return None, None


def find_nearby_value(regions, index, value_pattern, max_vertical=120):
    """Find the closest value region beside or below a label."""

    source = regions[index]
    source_box = get_bbox(source)
    candidates = []

    for candidate_index, candidate in enumerate(regions):

        if candidate_index == index:
            continue

        match = re.search(value_pattern, candidate["text"], re.IGNORECASE)

        if not match:
            continue

        candidate_box = get_bbox(candidate)
        vertical_distance = abs(center_y(candidate) - center_y(source))
        below_gap = top_y(candidate) - bottom_y(source)
        right_of_label = candidate_box.get("x", 0) >= (
            source_box.get("x", 0) + source_box.get("width", 0) - 12
        )
        same_line = vertical_distance <= max(
            source_box.get("height", 0),
            candidate_box.get("height", 0),
            18
        )
        directly_below = 0 <= below_gap <= max_vertical

        if not (same_line or directly_below):
            continue

        horizontal_distance = abs(center_x(candidate) - center_x(source))

        if same_line and not right_of_label:
            continue

        score = (
            (0 if same_line else 25)
            + vertical_distance
            + horizontal_distance * (0.25 if same_line else 0.05)
        )

        candidates.append((score, candidate_index, candidate, match.group(1)))

    candidates.sort(key=lambda item: item[0])

    if candidates:
        _, candidate_index, candidate, value = candidates[0]
        return candidate_index, candidate, value

    return None, None, None


def find_nearby_date(regions, index, max_regions=6):
    """
    Find a date near a declaration label.

    OCR may place the date:
      - directly below the label, or
      - on the same line / slightly to the right.

    No product-specific text is used here.
    """
    date_pattern = (
        r"([0-9]{1,2}[/-][0-9]{1,2}[/-][0-9]{2,4}"
        r"|[0-9]{1,2}[/-][0-9]{2,4}"
        r"|(?:JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)"
        r"[A-Z]*[ -]?[0-9]{2,4}"
        r"|[A-Z]{2,}[ -]?[0-9]{2,4})"
    )

    source = regions[index]
    candidates = []

    for next_index in range(
        index + 1,
        min(index + 1 + max_regions, len(regions))
    ):
        candidate = regions[next_index]
        text = candidate["text"]

        # Do not jump to a later unrelated declaration.
        if re.search(
            r"^(MFD|MFG|PKD|USE\s*BY|USEBY|"
            r"BEST\s*BEFORE|EXP(?:IRY)?|MRP|"
            r"BATCH|NET|FSSAI|LIC)\b",
            text,
            re.IGNORECASE
        ) and not re.search(date_pattern, text):
            break

        match = re.search(date_pattern, text)
        if not match:
            continue

        vertical_distance = abs(
            center_y(candidate) - center_y(source)
        )
        horizontal_distance = abs(
            center_x(candidate) - center_x(source)
        )

        # Date should be spatially close to its label.
        if vertical_distance > 100:
            continue

        if horizontal_distance > 220:
            continue

        score = (
            vertical_distance * 1.0
            + horizontal_distance * 0.35
        )

        candidates.append(
            (
                score,
                next_index,
                candidate,
                match.group(1)
            )
        )

    candidates.sort(key=lambda item: item[0])

    if candidates:
        _, next_index, candidate, date_value = candidates[0]
        return next_index, candidate, date_value

    return None, None, None

def is_label_or_metadata(text):
    """Identify OCR regions that should not become product names."""

    return bool(
        re.search(
            r"^(INGREDIENTS?|MANUFACTURED|"
            r"PACKED|IMPORTED|NET|MRP|BATCH|LOT|"
            r"MFD|MFG|PKD|USE|USEBY|BEST|EXP|"
            r"FSSAI|LIC|FOR CONSUMER|CONTACT|"
            r"PH|EMAIL|WEBSITE|MARKETED|"
            r"STORAGE|DIRECTIONS|NUTRITION|"
            r"FROM\s+MANUFACTURE|PRODUCT\s+OF|"
            r"BRAND\s+OWNED|INFORMATION\s+ON)",
            text,
            re.IGNORECASE
        )
    )


def is_ingredient_region(text):
    return bool(
        re.search(
            r"^INGREDIENTS?\s*:",
            text,
            re.IGNORECASE
        )
    )


def is_probable_organization_name(text):
    """Reject organization-like text as a commodity descriptor."""

    return bool(
        re.search(
            r"\b(?:PVT\.?|PRIVATE|LTD\.?|LIMITED|LLP|INC\.?|"
            r"CORP(?:ORATION)?\.?|COMPANY|CO\.?|GROUP|"
            r"HOLDINGS?|ENTERPRISES?|INDUSTRIES?|SONS?)\b",
            text,
            re.IGNORECASE
        )
    )


def is_probable_product_descriptor(text):
    """
    Detect a likely generic/product descriptor.

    Example:
        CHOCOLATE COOKIES

    It is preferred over words such as 'Flour' appearing
    inside an ingredients declaration.
    """

    if is_label_or_metadata(text):
        return False

    if is_ingredient_region(text):
        return False

    if is_probable_organization_name(text):
        return False

    if re.search(
        r"\b(MRP|NET|BATCH|MFD|MFG|USEBY|"
        r"FSSAI|LIC|MANUFACTURED|PACKED)\b",
        text,
        re.IGNORECASE
    ):
        return False

    words = text.split()

    if len(words) < 1 or len(words) > 4:
        return False

    # Strong signal: uppercase product descriptor.
    if (
        len(text) >= 4
        and text.upper() == text
        and re.search(r"[A-Z]", text)
    ):
        return True

    return False


def clean_product_name_candidate(text):
    """Strip obvious OCR garbage from a product-name candidate."""

    if not text:
        return text

    cleaned = text.strip()

    if not cleaned:
        return cleaned

    cleaned = re.sub(r"^[^A-Za-z]+", "", cleaned)
    cleaned = re.sub(r"[^A-Za-z0-9'&.-]+$", "", cleaned)

    words = cleaned.split()
    if len(words) >= 2 and len(words[0]) <= 2 and words[0].isalpha() and words[0].islower():
        cleaned = " ".join(words[1:])

    return cleaned.strip()


def is_probable_title_line(text):
    """Return True for a plausible package title line."""

    if is_label_or_metadata(text):
        return False

    if is_ingredient_region(text):
        return False

    if is_probable_organization_name(text):
        return False

    if not text:
        return False

    words = [word for word in text.split() if word]
    if len(words) < 2:
        return False

    if re.fullmatch(r"[A-Za-z][A-Za-z'&.-]*(?:\s+[A-Za-z][A-Za-z'&.-]*)+", text):
        return True

    if text.upper() == text and re.search(r"[A-Za-z]", text):
        return True

    return False


def extract_fields(ocr_data):

    product = {
        "product_name": None,
        "generic_name": None,
        "net_quantity": None,
        "mrp": None,
        "manufacturer": None,
        "address": None,
        "batch_number": None,
        "manufacturing_date": None,
        "use_by_date": None,
        "consumer_care_phone": None,
        "consumer_care_email": None,
        "inclusive_of_all_taxes": False,
        "evidence": {}
    }

    # =========================================================
    # PREPARE OCR REGIONS
    # =========================================================

    regions = []

    for region in ocr_data.get("regions", []):

        text = normalize_text(
            region.get("text", "")
        )

        if text:

            regions.append({
                "text": text,
                "bbox": region.get("bbox"),
                "confidence": region.get("confidence")
            })

    # =========================================================
    # PRODUCT NAME
    # =========================================================

    # First try adjacent OCR regions that form one name.
    # This is layout-driven and works for arbitrary brands,
    # e.g. "Nature's" + "Goodness".
    product_pair = None

    for index, region in enumerate(regions):

        text_value = region["text"]

        if top_y(region) > 250:
            continue

        if is_label_or_metadata(text_value):
            continue

        if is_ingredient_region(text_value):
            continue

        cleaned_value = clean_product_name_candidate(text_value)

        if not cleaned_value or not re.fullmatch(
            r"[A-Za-z][A-Za-z'&.-]*(?:\s+[A-Za-z][A-Za-z'&.-]*)*",
            cleaned_value
        ):
            continue

        if index + 1 >= len(regions):
            continue

        next_region = regions[index + 1]
        next_text = next_region["text"]
        cleaned_next_text = clean_product_name_candidate(next_text)

        if not cleaned_next_text or not re.fullmatch(
            r"[A-Za-z][A-Za-z'&.-]*(?:\s+[A-Za-z][A-Za-z'&.-]*)*",
            cleaned_next_text
        ):
            continue

        # Keep an uppercase category line separate from a title/logo line
        # so it can be selected as the generic commodity descriptor.
        if next_text.upper() == next_text:
            continue

        vertical_gap = (
            top_y(next_region) - bottom_y(region)
        )

        horizontal_distance = abs(
            center_x(next_region) - center_x(region)
        )

        if (
            0 <= vertical_gap <= 60
            and horizontal_distance <= 100
        ):
            product_pair = (
                {**region, "text": cleaned_value},
                {**next_region, "text": cleaned_next_text}
            )
            break

    if product_pair:
        region1, region2 = product_pair
        value = region1["text"] + " " + region2["text"]

        product["product_name"] = value

        product["evidence"]["product_name"] = (
            make_evidence(
                [region1, region2],
                value
            )
        )

    # If no adjacent pair exists, prefer explicit multi-word title lines
    # that clearly look like a pack title rather than metadata or brand
    # fragments. This covers cases such as "PUSHP GARAM MASALA".
    if product["product_name"] is None:

        title_candidates = []

        for index, region in enumerate(regions):

            text_value = region["text"]
            cleaned_text_value = clean_product_name_candidate(text_value)

            if top_y(region) > 250:
                continue

            if not cleaned_text_value or not is_probable_title_line(cleaned_text_value):
                continue

            score = (
                len(cleaned_text_value.split()) * 100
                - top_y(region)
                + (20 if cleaned_text_value.upper() == cleaned_text_value else 0)
            )

            title_candidates.append(
                (score, index, {**region, "text": cleaned_text_value})
            )

        if title_candidates:
            title_candidates.sort(key=lambda item: (-item[0], item[1]))
            _, _, region = title_candidates[0]

            product["product_name"] = region["text"]

            product["evidence"]["product_name"] = (
                make_evidence(
                    region,
                    region["text"]
                )
            )

    # If no title line exists, use the first plausible single-word
    # top-of-package OCR region.
    if product["product_name"] is None:

        candidates = []

        for index, region in enumerate(regions):

            text_value = region["text"]

            if top_y(region) > 250:
                continue

            if is_label_or_metadata(text_value):
                continue

            if is_ingredient_region(text_value):
                continue

            if is_probable_product_descriptor(text_value):
                continue

            if re.fullmatch(
                r"[A-Za-z][A-Za-z'&.-]*",
                text_value
            ):
                candidates.append(
                    (top_y(region), index, region)
                )

        candidates.sort(key=lambda item: item[0])

        if candidates:
            _, _, region = candidates[0]

            product["product_name"] = region["text"]

            product["evidence"]["product_name"] = (
                make_evidence(
                    region,
                    region["text"]
                )
            )

    # =========================================================
    # GENERIC NAME
    # =========================================================

    # Select a commodity from semantic keyword patterns, never from
    # arbitrary uppercase logo text or packaging instructions.
    generic_patterns = [
            r"\bgaram\s+masala\b",
            r"\bchocolate\s+syrup\b",
            r"\bmasala\b",
            r"\bbasmati\s+rice\b",
            r"\brace\b",
            r"\bspices?\b",
            r"\bbiscuits?\b",
            r"\bcookies?\b",
            r"\bflour\b",
            r"\bsalt\b",
            r"\bsugar\b",
            r"\btea\b",
            r"\bcoffee\b"
    ]

    for region in regions:

        text = region["text"]

        if is_ingredient_region(text):
            continue

        for pattern in generic_patterns:

            match = re.search(
                pattern,
                text,
                re.IGNORECASE
            )

            if match:

                value = match.group(0)

                if value.lower() == "garam masala":
                    value = "Garam Masala"
                elif value.lower() == "chocolate syrup":
                    value = "Chocolate Syrup"
                elif value.lower() == "basmati rice":
                    value = "Basmati Rice"
                elif value.lower() == "rice":
                    value = "Rice"
                elif value.isupper():
                    value = value.upper()
                else:
                    value = value.title()

                product["generic_name"] = value

                product["evidence"]["generic_name"] = (
                    make_evidence(
                        region,
                        value
                    )
                )

                break

        if product["generic_name"]:
            break

    # Layout fallback for non-food commodities: a short standalone
    # descriptor near the product name can be meaningful even when it is
    # outside the keyword vocabulary.
    if product["generic_name"] is None:
        product_name_regions = product["evidence"].get(
            "product_name", {}
        ).get("regions", [])

        product_name_bottom = 0

        if product_name_regions:
            product_name_bottom = max(
                region.get("bbox", {}).get("y", 0)
                + region.get("bbox", {}).get("height", 0)
                for region in product_name_regions
            )

        for region in regions:
            text = region["text"]
            words = text.split()

            if not 1 <= len(words) <= 3:
                continue

            if is_label_or_metadata(text):
                continue

            if is_probable_organization_name(text):
                continue

            if not re.fullmatch(r"[A-Za-z][A-Za-z&.-]*(?:\s+[A-Za-z][A-Za-z&.-]*)*", text):
                continue

            if text.upper() != text or top_y(region) < product_name_bottom:
                continue

            product["generic_name"] = text.title()
            product["evidence"]["generic_name"] = make_evidence(
                region,
                product["generic_name"]
            )
            break

    # =========================================================
    # NET QUANTITY
    # =========================================================

    quantity_pattern = re.compile(
        r"\b(\d+(?:\.\d+)?)\s*"
        r"(kg|g|mg|l|ml)\b",
        re.IGNORECASE
    )

    for index, region in enumerate(regions):

        match = quantity_pattern.search(
            region["text"]
        )

        if match:

            product["net_quantity"] = (
                match.group(1)
                + " "
                + match.group(2)
            )

            product["evidence"]["net_quantity"] = (
                make_evidence(
                    region,
                    product["net_quantity"]
                )
            )

            break

        if re.search(
            r"\bNET\s*(?:WT|WEIGHT|QUANTITY)\b",
            region["text"],
            re.IGNORECASE
        ):

            _, next_region = find_region_below(
                regions,
                index,
                max_gap=80,
                x_tolerance=120
            )

            if next_region:

                value_match = quantity_pattern.search(
                    next_region["text"]
                )

                if value_match:

                    product["net_quantity"] = (
                        value_match.group(1)
                        + " "
                        + value_match.group(2)
                    )

                    product["evidence"]["net_quantity"] = (
                        make_evidence(
                            [region, next_region],
                            product["net_quantity"]
                        )
                    )

                    break

    # =========================================================
    # MRP
    # =========================================================

    mrp_pattern = re.compile(
        r"MRP"
        r".{0,80}?"
        r"(?:₹|Rs\.?|INR)?\s*"
        r"(\d+(?:\.\d{1,2})?)",
        re.IGNORECASE
    )

    for index, region in enumerate(regions):

        match = mrp_pattern.search(
            region["text"]
        )

        if match:

            product["mrp"] = (
                "₹" + match.group(1)
            )

            product["evidence"]["mrp"] = (
                make_evidence(
                    region,
                    product["mrp"]
                )
            )

            break

        if re.search(
            r"\bMRP\b",
            region["text"],
            re.IGNORECASE
        ):

            _, next_region = find_region_below(
                regions,
                index,
                max_gap=80,
                x_tolerance=120
            )

            if next_region:

                value_match = re.search(
                    r"(?:₹|Rs\.?|INR)?\s*"
                    r"(\d+(?:\.\d{1,2})?)",
                    next_region["text"],
                    re.IGNORECASE
                )

                if value_match:

                    product["mrp"] = (
                        "₹"
                        + value_match.group(1)
                    )

                    product["evidence"]["mrp"] = (
                        make_evidence(
                            [region, next_region],
                            product["mrp"]
                        )
                    )

                    break

    # =========================================================
    # DATE PATTERN
    # =========================================================

    date_pattern = (
        r"([0-9]{1,2}[/-][0-9]{1,2}[/-][0-9]{2,4}"
        r"|[0-9]{1,2}[/-][0-9]{2,4}"
        r"|(?:JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)"
        r"[A-Z]*[ -]?[0-9]{2,4}"
        r"|[A-Z]{2,}[ -]?[0-9]{2,4})"
    )

    # =========================================================
    # MANUFACTURING DATE
    # =========================================================

    manufacturing_pattern = re.compile(
        r"(?:MFG\.?\s*DATE|MFD\.?|PKD|"
        r"MANUFACTURING\s*DATE|MANUFACTURED\s*DATE|"
        r"PACKED\s*DATE)"
        r"\s*[:.\-]?\s*"
        + date_pattern,
        re.IGNORECASE
    )

    for index, region in enumerate(regions):

        match = manufacturing_pattern.search(
            region["text"]
        )

        if match:

            product["manufacturing_date"] = (
                match.group(1)
            )

            product["evidence"]["manufacturing_date"] = (
                make_evidence(
                    region,
                    product["manufacturing_date"]
                )
            )

            break

        if re.search(
            r"\b(?:MFD|MFG|PKD|MANUFACTURING\s*DATE|"
            r"MANUFACTURED\s*DATE|PACKED\s*DATE)\b",
            region["text"],
            re.IGNORECASE
        ):

            _, next_region, date_value = find_nearby_value(
                regions,
                index,
                date_pattern
            )

            if date_value:

                product["manufacturing_date"] = (
                    date_value
                )

                product["evidence"]["manufacturing_date"] = (
                    make_evidence(
                        [region, next_region],
                        date_value
                    )
                )

                break

    # =========================================================
    # USE BY / EXPIRY
    # =========================================================

    use_pattern = re.compile(
        r"(?:USE\s*BY|USEBY|USE\s*BEFORE|BEST\s*BEFORE|"
        r"EXP(?:IRY)?|EXP\.?\s*DATE)"
        r"\s*[:.\-]?\s*"
        + date_pattern,
        re.IGNORECASE
    )

    for index, region in enumerate(regions):

        match = use_pattern.search(
            region["text"]
        )

        if match:

            product["use_by_date"] = (
                match.group(1)
            )

            product["evidence"]["use_by_date"] = (
                make_evidence(
                    region,
                    product["use_by_date"]
                )
            )

            break

        # Explicitly handles OCR:
        # USEBY:
        # 09/12/2024

        if re.search(
            r"\b(?:USE\s*BY|USEBY|USE\s*BEFORE|BEST\s*BEFORE|"
            r"EXP(?:IRY)?|EXP\.?\s*DATE)\b",
            region["text"],
            re.IGNORECASE
        ):

            _, next_region, date_value = find_nearby_value(
                regions,
                index,
                date_pattern
            )

            if date_value:

                product["use_by_date"] = (
                    date_value
                )

                product["evidence"]["use_by_date"] = (
                    make_evidence(
                        [region, next_region],
                        date_value
                    )
                )

                break

    # =========================================================
    # BATCH NUMBER
    # =========================================================

    batch_pattern = re.compile(
        r"\b(?:BATCH\s*(?:NO\.?|NUMBER)?|LOT\s*(?:NO\.?|NUMBER)?)"
        r"\s*[:\-]?\s*"
        r"([A-Za-z0-9][A-Za-z0-9/\-]{2,30})",
        re.IGNORECASE
    )

    invalid_batch_values = {
        "NO",
        "MFD",
        "MFG",
        "USE",
        "MRP",
        "NET",
        "PKD",
        "EXPIRY",
        "FSSAI"
    }

    batch_value_pattern = r"([A-Za-z0-9][A-Za-z0-9/\-]{2,30})"

    for index, region in enumerate(regions):

        match = batch_pattern.search(
            region["text"]
        )

        if match:

            value = match.group(1).strip()

            if value.upper() not in invalid_batch_values:

                product["batch_number"] = value

                product["evidence"]["batch_number"] = (
                    make_evidence(
                        region,
                        value
                    )
                )

                break

        if re.search(
            r"\b(?:BATCH\s*(?:NO\.?|NUMBER)?|LOT\s*(?:NO\.?|NUMBER)?)\b",
            region["text"],
            re.IGNORECASE
        ):
            _, next_region, value = find_nearby_value(
                regions,
                index,
                batch_value_pattern
            )

            if value and value.upper() not in invalid_batch_values:
                product["batch_number"] = value
                product["evidence"]["batch_number"] = make_evidence(
                    [region, next_region],
                    value
                )
                break

    # =========================================================
    # PHONE
    # =========================================================

    phone_patterns = [
        r"\+91[\s-]?\d{2,4}[\s-]?\d{6,8}",
        r"\+91[\s-]?[6-9]\d{9}",
        r"\b[6-9]\d{9}\b"
    ]

    for region in regions:

        for pattern in phone_patterns:

            match = re.search(
                pattern,
                region["text"]
            )

            if match:

                product["consumer_care_phone"] = (
                    match.group(0)
                )

                product["evidence"]["consumer_care_phone"] = (
                    make_evidence(
                        region,
                        match.group(0)
                    )
                )

                break

        if product["consumer_care_phone"]:
            break

    # =========================================================
    # EMAIL
    # =========================================================

    email_pattern = re.compile(
        r"[A-Za-z0-9._%+-]+"
        r"@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
        re.IGNORECASE
    )

    for region in regions:

        match = email_pattern.search(
            region["text"]
        )

        if match:

            product["consumer_care_email"] = (
                match.group(0)
            )

            product["evidence"]["consumer_care_email"] = (
                make_evidence(
                    region,
                    match.group(0)
                )
            )

            break

    # =========================================================
    # MANUFACTURER
    # =========================================================

    manufacturer_pattern = re.compile(
        r"(?:Manufactured\s*&\s*Packed\s*by|"
        r"Manufactured\s*by|"
        r"Packed\s*by|"
        r"Imported\s*by|"
        r"Importer)"
        r"\s*[:\-]?\s*(.*)",
        re.IGNORECASE
    )

    manufacturer_index = None
    manufacturer_region = None

    for index, region in enumerate(regions):

        match = manufacturer_pattern.search(
            region["text"]
        )

        if not match:
            continue

        manufacturer_index = index
        manufacturer_region = region

        inline_value = match.group(1).strip()

        if len(inline_value) >= 3:
            product["manufacturer"] = inline_value
            product["evidence"]["manufacturer"] = (
                make_evidence(region, inline_value)
            )
            break

        candidates = []

        for next_index in range(
            index + 1,
            min(index + 8, len(regions))
        ):

            candidate = regions[next_index]
            candidate_text = candidate["text"]

            vertical_gap = (
                top_y(candidate) - bottom_y(region)
            )

            if vertical_gap < 0:
                # Same-line candidate is still allowed.
                vertical_gap = abs(
                    center_y(candidate) - center_y(region)
                )

            if vertical_gap > 120:
                break

            horizontal_distance = abs(
                center_x(candidate) - center_x(region)
            )

            if horizontal_distance > 140:
                continue

            if is_ingredient_region(candidate_text):
                continue

            if re.search(
                r"^(NET|MRP|BATCH|MFD|MFG|USEBY|USE\s*BY|"
                r"FSSAI|LIC|FOR CONSUMER|PH|EMAIL|"
                r"CONTACT)",
                candidate_text,
                re.IGNORECASE
            ):
                continue

            # A manufacturer name is generally text-heavy.
            # Penalize regions dominated by digits.
            digit_count = sum(
                char.isdigit() for char in candidate_text
            )
            alpha_count = sum(
                char.isalpha() for char in candidate_text
            )

            if alpha_count == 0:
                continue

            digit_ratio = digit_count / max(
                len(candidate_text), 1
            )

            if digit_ratio > 0.35:
                continue

            # Prefer company-like text when available,
            # but do not require a specific company name.
            company_hint = bool(
                re.search(
                    r"\b(?:PVT|LTD|LIMITED|LLP|INC|"
                    r"CORP|CORPORATION|COMPANY|CO\.?)\b",
                    candidate_text,
                    re.IGNORECASE
                )
            )

            score = (
                vertical_gap * 1.0
                + horizontal_distance * 0.7
                - (40 if company_hint else 0)
            )

            candidates.append(
                (
                    score,
                    next_index,
                    candidate
                )
            )

        candidates.sort(
            key=lambda item: item[0]
        )

        if candidates:

            _, _, selected = candidates[0]

            value = selected["text"].strip()

            product["manufacturer"] = value

            product["evidence"]["manufacturer"] = (
                make_evidence(
                    [region, selected],
                    value
                )
            )

            break

    # =========================================================
    # MANUFACTURER ADDRESS
    # =========================================================

    if (
        manufacturer_index is not None
        and manufacturer_region is not None
    ):

        address_regions = []

        # Use the manufacturer value region when available as the
        # geometric anchor; otherwise use the label region.
        anchor = manufacturer_region

        # Determine the region immediately after the detected
        # manufacturer value. This avoids re-adding the company name
        # as an address line when the value was on a separate region.
        manufacturer_evidence_regions = (
            product["evidence"].get("manufacturer", {}).get("regions", [])
        )

        manufacturer_value_text = product.get("manufacturer")

        start_search = manufacturer_index + 1

        if manufacturer_value_text:
            for candidate_index in range(
                manufacturer_index + 1,
                min(manufacturer_index + 6, len(regions))
            ):
                if regions[candidate_index]["text"] == manufacturer_value_text:
                    start_search = candidate_index + 1
                    anchor = regions[candidate_index]
                    break

        previous_region = anchor

        stop_pattern = re.compile(
            r"^(?:MRP|BATCH|LOT|MFD|MFG|PKD|USEBY|USE\s*BY|"
            r"BEST\s*BEFORE|EXP(?:IRY)?|NET|FSSAI|LIC|"
            r"FOR CONSUMER|CONTACT|PH|EMAIL|E-MAIL|"
            r"WEBSITE|MARKETED|STORAGE|DIRECTIONS|NUTRITION)\b",
            re.IGNORECASE
        )

        for region in regions[start_search:]:

            text_value = region["text"]

            # Unrelated declarations may be interleaved in another column.
            # They must not terminate the manufacturer's visual address block.
            if not same_column(region, anchor, tolerance=90):
                continue

            # Stop at the next clearly identifiable declaration in this column.
            if stop_pattern.search(text_value):
                break

            # Ignore pure barcode / licence-like numeric strings.
            if re.fullmatch(r"\d{8,14}", text_value):
                continue

            vertical_gap = (
                top_y(region) - bottom_y(previous_region)
            )

            # Address lines should form a visually continuous block.
            if vertical_gap < -5:
                continue

            if vertical_gap > 45:
                # A large gap usually indicates a new section.
                break

            # Address-like content is detected structurally rather than
            # through specific cities/states/company names:
            # alphanumeric text, punctuation, or postal-code-like digits.
            has_alpha = bool(re.search(r"[A-Za-z]", text_value))
            has_digit = bool(re.search(r"\d", text_value))
            has_address_punctuation = bool(
                re.search(r"[,.\-/#()]", text_value)
            )

            if not (
                has_alpha
                and (
                    has_digit
                    or has_address_punctuation
                    or len(text_value.split()) >= 2
                )
            ):
                if address_regions:
                    break
                continue

            address_regions.append(region)
            previous_region = region

        if address_regions:

            address = " ".join(
                region["text"]
                for region in address_regions
            ).strip()

            product["address"] = address

            product["evidence"]["address"] = (
                make_evidence(
                    address_regions,
                    address
                )
            )

    # =========================================================
    # INCLUSIVE OF ALL TAXES
    # =========================================================

    tax_regions = []

    # OCR frequently confuses the capital "I" with lowercase "l"
    # (e.g. "Incl" -> "lncl"). Treat both spellings as equivalent
    # for pattern recognition while preserving the raw OCR evidence.
    inclusive_pattern = re.compile(
        r"(?:inclusive|incl|lncl)\s*\.?\s*"
        r"(?:of\s*)?all\s*tax(?:es)?",
        re.IGNORECASE
    )

    for region in regions:

        if inclusive_pattern.search(
            region["text"]
        ):

            tax_regions.append(region)
            break

    # Also support compact OCR such as:
    # MRPIncl.of all taxes:45.00
    # MRP(lncl.of all taxes):45.00
    if not tax_regions:

        compact_tax_pattern = re.compile(
            r"MRP.*?"
            r"(?:incl|lncl|inclusive)"
            r".*?"
            r"tax",
            re.IGNORECASE
        )

        for region in regions:

            if compact_tax_pattern.search(
                region["text"]
            ):

                tax_regions.append(region)
                break

    if tax_regions:

        product["inclusive_of_all_taxes"] = True

        product["evidence"][
            "inclusive_of_all_taxes"
        ] = make_evidence(
            tax_regions,
            True
        )

    return product