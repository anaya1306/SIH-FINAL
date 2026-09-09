import json
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    KeepTogether,
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


# ============================================================
# PATH CONFIGURATION
# ============================================================

# Current file is expected to be inside:
#
# SIH hackaton/
# ├── member 2/
# │   └── final_output.json
# │
# └── member 6/
#     └── pdf_generator.py
#
# Therefore:
# pdf_generator.py
#       ↓ parent
# member 6/
#       ↓ parent
# SIH hackaton/

BASE = Path(__file__).resolve().parent
PROJECT_ROOT = BASE.parent

MEMBER2_OUTPUT = PROJECT_ROOT / "member 2" / "final_output.json"

OUTPUT_PDF = BASE / "inspection_report.pdf"


# ============================================================
# FONT CONFIGURATION
# ============================================================

FONT = "Helvetica"
BOLD = "Helvetica-Bold"

font_candidates = [
    (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ),
    (
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
    ),
]

for regular_font, bold_font in font_candidates:
    if Path(regular_font).exists() and Path(bold_font).exists():
        try:
            pdfmetrics.registerFont(
                TTFont("ReportUnicode", regular_font)
            )
            pdfmetrics.registerFont(
                TTFont("ReportUnicodeBold", bold_font)
            )

            FONT = "ReportUnicode"
            BOLD = "ReportUnicodeBold"
            break

        except Exception:
            pass


# ============================================================
# GENERAL HELPERS
# ============================================================

def safe(value):
    """
    Convert values into safe printable strings.

    None / empty values are displayed as:
        Not Detected
    """

    if value is None or value == "":
        return "Not Detected"

    if isinstance(value, (dict, list)):
        return json.dumps(
            value,
            ensure_ascii=False
        )

    return str(value)


def first(dictionary, *keys):
    """
    Return the first non-empty value from the supplied keys.
    """

    if not isinstance(dictionary, dict):
        return None

    for key in keys:
        if dictionary.get(key) not in (None, ""):
            return dictionary[key]

    return None


def paragraph(value, style):
    """
    Create a safe ReportLab paragraph.
    """

    text = escape(safe(value))
    text = text.replace("\n", "<br/>")

    return Paragraph(text, style)


# ============================================================
# STYLES
# ============================================================

def build_styles():

    sheet = getSampleStyleSheet()

    return {

        "title": ParagraphStyle(
            "title",
            parent=sheet["Title"],
            fontName=BOLD,
            fontSize=17,
            leading=21,
            alignment=TA_CENTER,
            spaceAfter=3 * mm,
        ),

        "subtitle": ParagraphStyle(
            "subtitle",
            parent=sheet["Normal"],
            fontName=FONT,
            fontSize=8.5,
            leading=11,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#555555"),
            spaceAfter=6 * mm,
        ),

        "section": ParagraphStyle(
            "section",
            parent=sheet["Heading2"],
            fontName=BOLD,
            fontSize=10.5,
            leading=13,
            textColor=colors.white,
        ),

        "body": ParagraphStyle(
            "body",
            parent=sheet["BodyText"],
            fontName=FONT,
            fontSize=8.5,
            leading=11,
            spaceAfter=1.5 * mm,
        ),

        "small": ParagraphStyle(
            "small",
            parent=sheet["BodyText"],
            fontName=FONT,
            fontSize=7.3,
            leading=9.3,
        ),

        "small_bold": ParagraphStyle(
            "small_bold",
            parent=sheet["BodyText"],
            fontName=BOLD,
            fontSize=7.3,
            leading=9.3,
        ),

        "tiny": ParagraphStyle(
            "tiny",
            parent=sheet["BodyText"],
            fontName=FONT,
            fontSize=6.7,
            leading=8.4,
        ),
    }


# ============================================================
# SECTION HEADING
# ============================================================

def heading(text, styles):

    table = Table(
        [[Paragraph(escape(text), styles["section"])]],
        colWidths=[180 * mm],
    )

    table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, -1),
                    colors.HexColor("#243447"),
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    7,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    4,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    4,
                ),
            ]
        )
    )

    return table


# ============================================================
# GENERIC TABLE
# ============================================================

def grid(rows, widths, styles):

    processed_rows = []

    for row in rows:

        processed_row = []

        for cell in row:

            if isinstance(cell, Paragraph):
                processed_row.append(cell)
            else:
                processed_row.append(
                    paragraph(cell, styles["small"])
                )

        processed_rows.append(processed_row)

    table = Table(
        processed_rows,
        colWidths=widths,
        repeatRows=1,
    )

    table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor("#E9EEF2"),
                ),
                (
                    "FONTNAME",
                    (0, 0),
                    (-1, 0),
                    BOLD,
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.35,
                    colors.HexColor("#B7BEC5"),
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP",
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    5,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    5,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    4,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    4,
                ),
            ]
        )
    )

    return table


# ============================================================
# RULE SECTION
# ============================================================

def rule_section(title, items, styles):

    items = items if isinstance(items, list) else []

    content = [
        Paragraph(
            escape(title),
            styles["body"]
        )
    ]

    if not items:
        content.append(
            Paragraph(
                "None reported.",
                styles["small"]
            )
        )
        return [KeepTogether(content)]

    rows = [
        [
            "Rule ID",
            "Field",
            "Status",
            "Legal Requirement / Finding",
        ]
    ]

    for item in items:

        if not isinstance(item, dict):
            continue

        rows.append(
            [
                safe(first(item, "rule_id", "rule")),
                safe(first(item, "field", "field_name")),
                safe(first(item, "status")),
                safe(first(item, "description", "issue")),
            ]
        )

    table = grid(
        rows,
        [
            27 * mm,
            37 * mm,
            32 * mm,
            84 * mm,
        ],
        styles,
    )

    content.extend(
        [
            table,
            Spacer(1, 2 * mm),
        ]
    )

    return [KeepTogether(content)]


# ============================================================
# EVIDENCE NORMALIZATION
# ============================================================

def evidence_list(evidence):

    """
    Member 2 currently provides evidence in this form:

    {
        "field_name": {
            "value": "...",
            "source_text": "...",
            "regions": [...]
        }
    }

    Normalize that into a list so the PDF generator can
    work with it easily.
    """

    if isinstance(evidence, list):

        return [
            item
            for item in evidence
            if isinstance(item, dict)
        ]

    if isinstance(evidence, dict):

        output = []

        for field_name, value in evidence.items():

            if not isinstance(value, dict):
                value = {
                    "value": value
                }

            item = dict(value)

            item.setdefault(
                "field_name",
                field_name
            )

            # ------------------------------------------------
            # Convert Member 2's regions into individual
            # evidence records.
            # ------------------------------------------------

            regions = item.get("regions")

            if isinstance(regions, list) and regions:

                for region in regions:

                    if not isinstance(region, dict):
                        continue

                    region_item = dict(item)

                    region_item["region"] = region

                    region_item["bounding_box"] = (
                        region.get("bbox")
                    )

                    region_item["confidence"] = (
                        region.get("confidence")
                    )

                    region_item["ocr_source_text"] = (
                        region.get("text")
                        or item.get("source_text")
                    )

                    output.append(region_item)

            else:

                output.append(item)

        return output

    return []


# ============================================================
# BOUNDING BOX FORMATTER
# ============================================================

def format_bbox(value):

    if isinstance(value, dict):

        return (
            f"x={safe(value.get('x'))}, "
            f"y={safe(value.get('y'))}, "
            f"width={safe(first(value, 'width', 'w'))}, "
            f"height={safe(first(value, 'height', 'h'))}"
        )

    if isinstance(value, (list, tuple)) and len(value) >= 4:

        return (
            f"x={value[0]}, "
            f"y={value[1]}, "
            f"width={value[2]}, "
            f"height={value[3]}"
        )

    return "Not Detected"


# ============================================================
# FOOTER
# ============================================================

def footer(canvas, document):

    canvas.saveState()

    width, _ = A4

    canvas.setStrokeColor(
        colors.HexColor("#B8B8B8")
    )

    canvas.line(
        15 * mm,
        13 * mm,
        width - 15 * mm,
        13 * mm,
    )

    canvas.setFont(
        FONT,
        7.2
    )

    canvas.setFillColor(
        colors.HexColor("#555555")
    )

    canvas.drawString(
        15 * mm,
        8.5 * mm,
        "Generated by Packaged Commodity Compliance System",
    )

    canvas.drawRightString(
        width - 15 * mm,
        8.5 * mm,
        f"Page {document.page}",
    )

    canvas.restoreState()


# ============================================================
# MAIN PDF GENERATOR
# ============================================================

def generate_pdf(
    input_json=MEMBER2_OUTPUT,
    output_pdf=OUTPUT_PDF,
):

    input_json = Path(input_json)
    output_pdf = Path(output_pdf)

    # --------------------------------------------------------
    # Validate input
    # --------------------------------------------------------

    if not input_json.exists():

        raise FileNotFoundError(
            "\nMember 2 final_output.json was not found.\n"
            f"Expected location:\n{input_json}\n\n"
            "Make sure pipeline_test.py has generated "
            "final_output.json before running the PDF generator."
        )

    # --------------------------------------------------------
    # Load Member 2 JSON
    # --------------------------------------------------------

    with input_json.open(
        "r",
        encoding="utf-8"
    ) as file:

        data = json.load(file)

    # --------------------------------------------------------
    # Read standard sections
    # --------------------------------------------------------

    inspection = data.get("inspection") or {}
    product = data.get("product") or {}
    field_status = data.get("field_status") or {}
    compliance = data.get("compliance") or {}
    evidence = evidence_list(
        data.get("evidence")
    )
    ocr = data.get("ocr") or {}

    styles = build_styles()

    story = []

    # ========================================================
    # TITLE
    # ========================================================

    story.extend(
        [
            Paragraph(
                "PACKAGED COMMODITY INSPECTION REPORT",
                styles["title"],
            ),

            Paragraph(
                "Preliminary OCR-based compliance screening report",
                styles["subtitle"],
            ),
        ]
    )

    # ========================================================
    # INSPECTION INFORMATION
    # ========================================================

    story.append(
        heading(
            "INSPECTION INFORMATION",
            styles,
        )
    )

    inspection_rows = [
        ["Field", "Value"],
        [
            "Inspection ID",
            safe(
                inspection.get(
                    "inspection_id"
                )
            ),
        ],
        [
            "Date / Time",
            safe(
                inspection.get(
                    "date_time"
                )
            ),
        ],
        [
            "System Name",
            safe(
                first(
                    inspection,
                    "system_name"
                )
            ),
        ],
    ]

    story.append(
        grid(
            inspection_rows,
            [
                55 * mm,
                125 * mm,
            ],
            styles,
        )
    )

    story.append(
        heading(
            "PRODUCT INFORMATION",
            styles,
        )
    )

    # ========================================================
    # PRODUCT FIELDS
    # ========================================================

    product_fields = [
        ("Product Name", "product_name"),
        ("Generic Name", "generic_name"),
        ("Net Quantity", "net_quantity"),
        ("MRP", "mrp"),
        ("Manufacturer", "manufacturer"),
        ("Address", "address"),
        ("Batch Number", "batch_number"),
        ("Manufacturing Date", "manufacturing_date"),
        ("Use By Date", "use_by_date"),
        ("Consumer Care Phone", "consumer_care_phone"),
        ("Consumer Care Email", "consumer_care_email"),
        (
            "Inclusive of All Taxes",
            "inclusive_of_all_taxes",
        ),
    ]

    product_rows = [
        ["Field", "Value"]
    ]

    for label, key in product_fields:

        product_rows.append(
            [
                label,
                safe(product.get(key)),
            ]
        )

    story.append(
        grid(
            product_rows,
            [
                55 * mm,
                125 * mm,
            ],
            styles,
        )
    )

    # ========================================================
    # COMPLIANCE SUMMARY
    # ========================================================

    story.append(
        heading(
            "COMPLIANCE SUMMARY",
            styles,
        )
    )

    passed = (
        compliance.get("passed")
        if isinstance(
            compliance.get("passed"),
            list
        )
        else []
    )

    potential_violations = (
        compliance.get("potential_violations")
        if isinstance(
            compliance.get("potential_violations"),
            list
        )
        else []
    )

    needs_review = (
        compliance.get("needs_review")
        if isinstance(
            compliance.get("needs_review"),
            list
        )
        else []
    )

    detected_fields = sum(
        1
        for value in field_status.values()
        if isinstance(value, dict)
        and value.get("status") == "FOUND"
    )

    summary_rows = [
        ["Summary", "Result"],
        [
            "Overall Status",
            safe(
                compliance.get(
                    "overall_status"
                )
            ),
        ],
        [
            "Detected Fields",
            str(detected_fields),
        ],
        [
            "Passed Checks",
            str(len(passed)),
        ],
        [
            "Potential Issues",
            str(
                len(
                    potential_violations
                )
            ),
        ],
        [
            "Needs Review",
            str(len(needs_review)),
        ],
    ]

    story.append(
        grid(
            summary_rows,
            [
                55 * mm,
                125 * mm,
            ],
            styles,
        )
    )

    story.append(
        Spacer(
            1,
            3 * mm
        )
    )

    # ========================================================
    # RULE RESULTS
    # ========================================================

    story.extend(
        rule_section(
            "Passed Checks / Rules",
            passed,
            styles,
        )
    )

    story.append(
        Spacer(
            1,
            2 * mm
        )
    )

    story.extend(
        rule_section(
            "Potential Violations / Potential Issues",
            potential_violations,
            styles,
        )
    )

    story.append(
        Spacer(
            1,
            2 * mm
        )
    )

    story.extend(
        rule_section(
            "Needs Review",
            needs_review,
            styles,
        )
    )

    # ========================================================
    # PAGE 2
    # ========================================================

    story.append(PageBreak())

    story.append(
        heading(
            "EVIDENCE / OCR VERIFICATION",
            styles,
        )
    )

    story.append(
        Spacer(
            1,
            3 * mm
        )
    )

    # ========================================================
    # EVIDENCE
    # ========================================================

    if evidence:

        for index, item in enumerate(
            evidence,
            start=1
        ):

            field_name = first(
                item,
                "field_name",
                "field",
                "detected_field",
            )

            detected_value = first(
                item,
                "value",
                "detected_value",
                "detected",
            )

            source_text = first(
                item,
                "source_text",
                "ocr_source_text",
                "source",
                "ocr_text",
            )

            confidence = first(
                item,
                "confidence",
                "score",
            )

            bounding_box = first(
                item,
                "bounding_box",
                "bbox",
                "box",
            )

            rows = [
                [
                    "Field Name",
                    safe(field_name),
                ],
                [
                    "Detected Value",
                    safe(detected_value),
                ],
                [
                    "Source OCR Text",
                    safe(source_text),
                ],
                [
                    "Confidence",
                    safe(confidence),
                ],
                [
                    "Bounding Box",
                    format_bbox(
                        bounding_box
                    ),
                ],
            ]

            table = Table(
                [
                    [
                        paragraph(
                            key,
                            styles["small_bold"],
                        ),
                        paragraph(
                            value,
                            styles["small"],
                        ),
                    ]
                    for key, value in rows
                ],
                colWidths=[
                    42 * mm,
                    138 * mm,
                ],
            )

            table.setStyle(
                TableStyle(
                    [
                        (
                            "BACKGROUND",
                            (0, 0),
                            (0, -1),
                            colors.HexColor("#F2F4F5"),
                        ),
                        (
                            "GRID",
                            (0, 0),
                            (-1, -1),
                            0.35,
                            colors.HexColor("#C4CBD1"),
                        ),
                        (
                            "VALIGN",
                            (0, 0),
                            (-1, -1),
                            "TOP",
                        ),
                        (
                            "LEFTPADDING",
                            (0, 0),
                            (-1, -1),
                            5,
                        ),
                        (
                            "RIGHTPADDING",
                            (0, 0),
                            (-1, -1),
                            5,
                        ),
                        (
                            "TOPPADDING",
                            (0, 0),
                            (-1, -1),
                            4,
                        ),
                        (
                            "BOTTOMPADDING",
                            (0, 0),
                            (-1, -1),
                            4,
                        ),
                    ]
                )
            )

            story.extend(
                [
                    Paragraph(
                        f"Evidence Region {index}",
                        styles["body"],
                    ),
                    table,
                    Spacer(
                        1,
                        4 * mm
                    ),
                ]
            )

    else:

        story.append(
            Paragraph(
                "No evidence regions were provided.",
                styles["body"],
            )
        )

    # ========================================================
    # OCR INFORMATION
    # ========================================================

    story.append(
        heading(
            "OCR INFORMATION",
            styles,
        )
    )

    story.append(
        Spacer(
            1,
            2 * mm
        )
    )

    low_confidence = (
        ocr.get("low_confidence_fields")
        if isinstance(
            ocr,
            dict
        )
        and isinstance(
            ocr.get(
                "low_confidence_fields"
            ),
            list,
        )
        else []
    )

    low_confidence_text = "; ".join(
        (
            f"{safe(first(item, 'field', 'field_name'))} "
            f"({safe(first(item, 'confidence', 'score'))})"
        )
        for item in low_confidence
        if isinstance(item, dict)
    )

    if not low_confidence_text:
        low_confidence_text = "None reported"

    ocr_rows = [
        ["Field", "Value"],
        [
            "OCR Engine",
            safe(
                first(
                    ocr,
                    "engine",
                    "ocr_engine",
                )
            ),
        ],
        [
            "Overall Confidence",
            safe(
                first(
                    ocr,
                    "overall_confidence",
                    "confidence",
                )
            ),
        ],
        [
            "Low-Confidence Fields",
            low_confidence_text,
        ],
    ]

    story.append(
        grid(
            ocr_rows,
            [
                55 * mm,
                125 * mm,
            ],
            styles,
        )
    )

    # ========================================================
    # RAW OCR
    # ========================================================

    raw_ocr = first(
        ocr,
        "raw_text",
        "full_text",
    )

    if raw_ocr:

        story.extend(
            [
                Spacer(
                    1,
                    2 * mm
                ),

                Paragraph(
                    "Original OCR Text",
                    styles["body"],
                ),

                Paragraph(
                    escape(
                        safe(raw_ocr)
                    ).replace(
                        "\n",
                        "<br/>"
                    ),
                    styles["tiny"],
                ),
            ]
        )

    # ========================================================
    # DECLARATION CHECKLIST
    # ========================================================

    checklist_fields = [
        (
            "Manufacturer / Packer / Importer",
            "manufacturer",
            "manufacturer",
        ),
        (
            "Generic Name",
            "generic_name",
            "generic_name",
        ),
        (
            "Net Quantity",
            "net_quantity",
            "net_quantity",
        ),
        (
            "MRP",
            "mrp",
            "mrp",
        ),
        (
            "Manufacturing / Packing Date",
            "manufacturing_date",
            "manufacturing_date",
        ),
        (
            "Use By / Expiry Date",
            "use_by_date",
            "use_by_date",
        ),
        (
            "Consumer Care Details",
            "consumer_care",
            "consumer_care_phone",
        ),
        (
            "Batch / Lot Number",
            "batch_number",
            "batch_number",
        ),
    ]

    checklist_rows = [
        [
            "Declaration",
            "Status",
            "Detected Value",
        ]
    ]

    for label, key, value_key in checklist_fields:

        field = field_status.get(key)

        if isinstance(field, dict):
            status = safe(
                field.get("status")
            )
        else:
            status = "NOT_DETECTED"

        if status == "FOUND":
            mark = "✓"
        elif status in (
            "NEEDS_REVIEW",
            "POTENTIAL_VIOLATION",
            "NOT_DETECTED",
        ):
            mark = "⚠"
        else:
            mark = "—"

        checklist_rows.append(
            [
                f"{mark}  {label}",
                status,
                safe(
                    product.get(
                        value_key
                    )
                ),
            ]
        )

    story.extend(
        [
            Spacer(
                1,
                5 * mm
            ),

            heading(
                "DECLARATION CHECKLIST",
                styles,
            ),

            Spacer(
                1,
                2 * mm
            ),

            grid(
                checklist_rows,
                [
                    78 * mm,
                    37 * mm,
                    65 * mm,
                ],
                styles,
            ),
        ]
    )

    # ========================================================
    # INSPECTOR VERIFICATION
    # ========================================================

    story.extend(
        [
            Spacer(
                1,
                5 * mm
            ),

            heading(
                "INSPECTOR VERIFICATION",
                styles,
            ),

            Spacer(
                1,
                2 * mm
            ),
        ]
    )

    verification_rows = [
        [
            "Verification Outcome",
            "☐ Verified Compliant    "
            "☐ Potential Non-Compliance Confirmed    "
            "☐ Requires Further Inspection",
        ],
        [
            "Inspector Name",
            "____________________________________________",
        ],
        [
            "Remarks",
            "______________________________________________________________\n"
            "______________________________________________________________",
        ],
        [
            "Signature",
            "____________________________________________",
        ],
        [
            "Date",
            "________________________",
        ],
    ]

    story.append(
        grid(
            verification_rows,
            [
                48 * mm,
                132 * mm,
            ],
            styles,
        )
    )

    # ========================================================
    # DISCLAIMER
    # ========================================================

    story.extend(
        [
            Spacer(
                1,
                6 * mm
            ),

            heading(
                "DISCLAIMER",
                styles,
            ),
        ]
    )

    disclaimer = (
        "This report presents preliminary OCR-based screening "
        "findings only. 'NEEDS_REVIEW' and "
        "'POTENTIAL_VIOLATION' are system screening statuses "
        "and are not final legal decisions. OCR results may "
        "contain recognition errors. Final verification and "
        "any legal determination must be performed by an "
        "authorized inspector after reviewing the product "
        "and label evidence."
    )

    disclaimer_box = Table(
        [
            [
                paragraph(
                    disclaimer,
                    styles["small"],
                )
            ]
        ],
        colWidths=[
            180 * mm
        ],
    )

    disclaimer_box.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, -1),
                    colors.HexColor("#F7F7F7"),
                ),
                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.HexColor("#B7BEC5"),
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    7,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    7,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    7,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    7,
                ),
            ]
        )
    )

    story.append(
        disclaimer_box
    )

    # ========================================================
    # BUILD PDF
    # ========================================================

    output_pdf.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    document = SimpleDocTemplate(
        str(output_pdf),
        pagesize=A4,
        rightMargin=15 * mm,
        leftMargin=15 * mm,
        topMargin=15 * mm,
        bottomMargin=18 * mm,
        title="Packaged Commodity Inspection Report",
    )

    document.build(
        story,
        onFirstPage=footer,
        onLaterPages=footer,
    )

    return output_pdf


# ============================================================
# COMMAND LINE ENTRY
# ============================================================

if __name__ == "__main__":

    try:

        generated_file = generate_pdf()

        print(
            "\nPDF generated successfully!"
        )

        print(
            f"Input JSON : {MEMBER2_OUTPUT}"
        )

        print(
            f"Output PDF : {generated_file}"
        )

    except Exception as error:

        print(
            "\nPDF generation failed."
        )

        print(
            f"Error: {error}"
        )

        raise