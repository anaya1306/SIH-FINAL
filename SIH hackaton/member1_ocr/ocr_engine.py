"""
ocr_engine.py
-------------
Member 1's core module: runs PaddleOCR on a product/package image and
returns RAW OCR results in the standardized JSON contract that
Member 2's NLP/extraction module consumes.

This file is intentionally the ONLY place that talks to PaddleOCR.
preprocessing.py never imports paddleocr, and test_ocr.py never calls
PaddleOCR directly - everything goes through run_ocr() below.

Nothing in this file corrects, normalizes, or rewrites OCR text.
Whatever PaddleOCR returns is what gets put in "text" and "full_text".
"""

import os
import re

import cv2
import numpy as np

import config
import preprocessing as pp

try:
    from paddleocr import PaddleOCR
except ImportError as e:  # pragma: no cover
    PaddleOCR = None
    _PADDLE_IMPORT_ERROR = e
else:
    _PADDLE_IMPORT_ERROR = None


class OCREngineError(Exception):
    """Raised for expected, user-facing failures (bad path, bad image, etc.)."""
    pass


# ------------------------------------------------------------------
# PaddleOCR lifecycle (loaded once, reused across calls)
# ------------------------------------------------------------------

_ocr_instance = None


def get_ocr_instance():
    """Lazily create and cache a single PaddleOCR instance."""
    global _ocr_instance

    if PaddleOCR is None:
        raise OCREngineError(
            "paddleocr is not installed. Run: pip install -r requirements.txt "
            f"(original import error: {_PADDLE_IMPORT_ERROR})"
        )

    if _ocr_instance is None:
        _ocr_instance = PaddleOCR(
            use_angle_cls=config.USE_ANGLE_CLS,
            lang=config.OCR_LANG,
            use_gpu=config.USE_GPU,
            show_log=False,
        )
    return _ocr_instance


# ------------------------------------------------------------------
# Image loading
# ------------------------------------------------------------------

def _load_image(image_path):
    if not isinstance(image_path, str) or not image_path.strip():
        raise OCREngineError("No image path provided.")

    if not os.path.isfile(image_path):
        raise OCREngineError(f"Image not found: {image_path}")

    # cv2.imread returns None instead of raising on unreadable/corrupt/
    # unsupported files, so we check explicitly for a clear error.
    image = cv2.imread(image_path)
    if image is None:
        raise OCREngineError(
            f"Could not read image (corrupt, unsupported format, or not "
            f"actually an image file): {image_path}"
        )
    return image


# ------------------------------------------------------------------
# Bounding box helpers
# ------------------------------------------------------------------

def _polygon_to_bbox(polygon_points):
    """Convert a 4-point (or N-point) polygon to an axis-aligned x/y/w/h box."""
    xs = [p[0] for p in polygon_points]
    ys = [p[1] for p in polygon_points]

    x_min, x_max = min(xs), max(xs)
    y_min, y_max = min(ys), max(ys)

    return {
        "x": int(round(x_min)),
        "y": int(round(y_min)),
        "width": int(round(x_max - x_min)),
        "height": int(round(y_max - y_min)),
    }


def _sort_reading_order(regions):
    """
    Group regions into rough horizontal "rows" (by vertical center
    proximity), then sort left-to-right within each row, and rows
    top-to-bottom. This is a heuristic - good enough for constructing
    a sensible full_text reading order, not a layout engine.
    """
    if not regions:
        return regions

    ordered_input = sorted(
        regions, key=lambda r: (r["bbox"]["y"], r["bbox"]["x"])
    )

    rows = []
    for region in ordered_input:
        bbox = region["bbox"]
        center_y = bbox["y"] + bbox["height"] / 2.0

        placed = False
        for row in rows:
            ref_bbox = row[0]["bbox"]
            ref_center_y = ref_bbox["y"] + ref_bbox["height"] / 2.0
            avg_height = (ref_bbox["height"] + bbox["height"]) / 2.0
            avg_height = max(avg_height, 1)

            if abs(center_y - ref_center_y) <= 0.6 * avg_height:
                row.append(region)
                placed = True
                break

        if not placed:
            rows.append([region])

    rows.sort(key=lambda row: min(r["bbox"]["y"] for r in row))

    ordered = []
    for row in rows:
        ordered.extend(sorted(row, key=lambda r: r["bbox"]["x"]))

    return ordered


def _ocr_quality_score(page_result):
    """Score raw OCR output using orientation-independent quality signals."""

    if not page_result:
        return float("-inf")

    readable_chars = 0
    total_chars = 0
    confidence_total = 0.0
    horizontal_regions = 0
    shape_quality_total = 0.0
    useful_labels = 0

    label_pattern = re.compile(
        r"\b(?:MRP|MFG|MFD|PKD|BATCH|LOT|USE|BEST|EXP|NET|"
        r"MANUFACTURED|CONTENT|QUANTITY|LIC)\b",
        re.IGNORECASE
    )

    for line in page_result:
        try:
            polygon, (text, confidence) = line
            points = np.asarray(polygon, dtype=np.float32)
        except (TypeError, ValueError):
            continue

        text = str(text or "")
        alphanumeric = sum(char.isalnum() for char in text)
        readable_chars += alphanumeric
        total_chars += len(text.strip())
        confidence_total += float(confidence)

        if points.size and points.shape[0] >= 4:
            width = np.linalg.norm(points[1] - points[0])
            height = np.linalg.norm(points[3] - points[0])
            shape_quality_total += min(
                width / max(height, 1.0),
                1.0
            )
            if width >= height:
                horizontal_regions += 1

        if label_pattern.search(text):
            useful_labels += 1

    region_count = len(page_result)
    if not region_count:
        return float("-inf")

    average_confidence = confidence_total / region_count
    readable_ratio = readable_chars / max(total_chars, 1)
    horizontal_ratio = horizontal_regions / region_count
    shape_quality = shape_quality_total / region_count

    return (
        region_count * 1.5
        + readable_chars * 0.05
        + average_confidence * 20
        + readable_ratio * 10
        + horizontal_ratio * 15
        + shape_quality * 25
        + useful_labels * 20
    )


def _convert_page_result(page_result, input_transform, orig_w, orig_h):
    """Convert one PaddleOCR page into the public region contract."""

    regions = []

    for line in page_result:
        try:
            polygon, (text, confidence) = line
        except (TypeError, ValueError):
            continue

        try:
            mapped_points = pp.map_points_to_original(polygon, input_transform)
        except Exception:
            mapped_points = np.array(polygon, dtype=np.float32)

        mapped_points[:, 0] = np.clip(mapped_points[:, 0], 0, orig_w)
        mapped_points[:, 1] = np.clip(mapped_points[:, 1], 0, orig_h)

        regions.append(
            {
                "text": text,
                "bbox": _polygon_to_bbox(mapped_points.tolist()),
                "confidence": round(float(confidence), 4),
            }
        )

    return regions


# ------------------------------------------------------------------
# Main entry point
# ------------------------------------------------------------------

def run_ocr(image_path, use_preprocessed=None):
    """
    Run the full Member 1 pipeline on a single image and return the
    standardized JSON-serializable dict:

        {
            "engine": "paddle",
            "image_size": {"width": ..., "height": ...},
            "regions": [{"text", "bbox", "confidence"}, ...],
            "full_text": "..."
        }

    On any handled failure, returns:

        {"error": "<message>", "engine": "paddle"}

    instead of raising, so callers (Member 2, test scripts, etc.) can
    always safely do json.dumps() on the result.

    use_preprocessed:
        None  -> use config.USE_PREPROCESSED_IMAGE (default)
        True  -> force OCR to run on the preprocessed image
        False -> force OCR to run on the original, untouched image
    """
    if use_preprocessed is None:
        use_preprocessed = config.USE_PREPROCESSED_IMAGE

    # ---- 1. Load original image (never overwritten) ----
    try:
        original_image = _load_image(image_path)
    except OCREngineError as e:
        return {"error": str(e), "engine": "paddle"}

    orig_h, orig_w = original_image.shape[:2]

    # ---- 2. Preprocess (on a copy; original_image is untouched) ----
    try:
        processed_image, transform = pp.preprocess_pipeline(
            original_image, steps=config.PREPROCESS_STEPS, cfg=config
        )
    except Exception as e:
        # Preprocessing is a "best effort" enhancement. If it breaks
        # for any reason, fall back to running OCR on the original
        # image rather than failing the whole request.
        processed_image = original_image.copy()
        transform = pp.identity_transform()

    if use_preprocessed:
        ocr_input_image = processed_image
        input_transform = transform
    else:
        ocr_input_image = original_image
        input_transform = pp.identity_transform()

    # ---- 3. Run PaddleOCR on orientation candidates ----
    try:
        ocr = get_ocr_instance()
    except OCREngineError as e:
        return {"error": str(e), "engine": "paddle"}

    angles = getattr(config, "ORIENTATION_ANGLES", (0,))
    if not getattr(config, "USE_ORIENTATION_SEARCH", False):
        angles = (0,)

    candidates = []

    for angle in angles:
        try:
            candidate_image, orientation_matrix = pp.rotate_orientation(
                ocr_input_image,
                angle
            )
            candidate_transform = dict(input_transform)
            candidate_transform["orientation_matrix"] = orientation_matrix
            raw_result = ocr.ocr(
                candidate_image,
                cls=config.USE_ANGLE_CLS
            )
        except Exception as e:
            if len(angles) == 1:
                return {"error": f"OCR engine failure: {e}", "engine": "paddle"}
            continue

        page_result = raw_result[0] if raw_result else None
        if page_result is None:
            page_result = []

        candidates.append(
            (
                _ocr_quality_score(page_result),
                angle,
                page_result,
                candidate_transform
            )
        )

    if not candidates:
        return {"error": "OCR engine failure: no orientation candidate succeeded.", "engine": "paddle"}

    _, _, page_result, input_transform = max(
        candidates,
        key=lambda candidate: candidate[0]
    )

    if not page_result:
        return {
            "engine": "paddle",
            "image_size": {"width": orig_w, "height": orig_h},
            "regions": [],
            "full_text": "",
            "warning": "No text detected in image.",
        }

    # ---- 4. Convert every detection to the standard region format ----
    regions = _convert_page_result(
        page_result,
        input_transform,
        orig_w,
        orig_h
    )

    if not regions:
        return {
            "engine": "paddle",
            "image_size": {"width": orig_w, "height": orig_h},
            "regions": [],
            "full_text": "",
            "warning": "OCR ran but produced no usable regions.",
        }

    # ---- 5. Order regions into a reading order and build full_text ----
    ordered_regions = _sort_reading_order(regions)
    full_text = "\n".join(region["text"] for region in ordered_regions)

    return {
        "engine": "paddle",
        "image_size": {"width": orig_w, "height": orig_h},
        "regions": ordered_regions,
        "full_text": full_text,
    }
