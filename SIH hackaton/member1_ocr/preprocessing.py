"""
preprocessing.py
-----------------
Modular image preprocessing for Member 1's OCR pipeline.

Design goals:
- NEVER mutate the caller's original image (always work on copies).
- Every geometry-changing step (resize, deskew) records how to map a
  point in the *processed* image back to the *original* image, so
  ocr_engine.py can produce bounding boxes in original image
  coordinates, exactly as the JSON contract requires.
- Each step is a small, independent function so it can be tuned or
  swapped out later without touching the rest of the pipeline.

Pipeline order: resize -> glare removal -> illumination correction ->
contrast enhancement -> deskew -> sharpen.

Only resize and deskew change image geometry. glare removal,
illumination correction, contrast enhancement and sharpening only
change pixel values, not the coordinate system.
"""

import cv2
import numpy as np


def identity_transform():
    """Transform representing 'no geometric change at all'."""
    return {
        "scale_x": 1.0,
        "scale_y": 1.0,
        "rotation_matrix": None,  # 2x3 affine matrix used by cv2.warpAffine, or None
        "orientation_matrix": None,  # candidate orientation -> source frame
    }


# ------------------------------------------------------------------
# Individual preprocessing steps
# ------------------------------------------------------------------

def resize_image(image, max_dimension):
    """
    Resize so the longest side == max_dimension (only shrinks, never
    upscales). Returns (resized_image, scale_x, scale_y) where
    scale_x/scale_y are the factors to multiply a point in the
    RESIZED image by, to get the point in the ORIGINAL image.
    """
    if max_dimension is None:
        return image, 1.0, 1.0

    h, w = image.shape[:2]
    longest_side = max(h, w)

    if longest_side <= max_dimension:
        return image, 1.0, 1.0

    scale = max_dimension / float(longest_side)
    new_w = max(1, int(round(w * scale)))
    new_h = max(1, int(round(h * scale)))

    resized = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)

    scale_x = w / float(new_w)
    scale_y = h / float(new_h)
    return resized, scale_x, scale_y


def remove_glare(image, brightness_threshold=235):
    """
    Detect very bright hotspots (typical of glare off plastic/foil
    packaging) and inpaint them using neighboring pixels.
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, glare_mask = cv2.threshold(
        gray, brightness_threshold, 255, cv2.THRESH_BINARY
    )

    # If there's basically no glare, skip inpainting (it's slow and
    # can slightly blur text if applied unnecessarily).
    if cv2.countNonZero(glare_mask) < 25:
        return image

    kernel = np.ones((3, 3), np.uint8)
    glare_mask = cv2.dilate(glare_mask, kernel, iterations=2)

    inpainted = cv2.inpaint(image, glare_mask, 3, cv2.INPAINT_TELEA)
    return inpainted


def correct_illumination(image, blur_sigma=25):
    """
    Normalize uneven lighting (shadows, gradients across a curved
    package) by estimating the background illumination with a large
    Gaussian blur and dividing it out, on the L channel only (LAB
    color space) so color information is preserved.
    """
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    l_channel, a_channel, b_channel = cv2.split(lab)

    l_float = l_channel.astype(np.float32)
    background = cv2.GaussianBlur(l_float, (0, 0), blur_sigma)
    background = np.where(background <= 0, 1, background)  # avoid div-by-zero

    normalized = (l_float / background) * 200.0
    normalized = np.clip(normalized, 0, 255).astype(np.uint8)

    corrected_lab = cv2.merge((normalized, a_channel, b_channel))
    corrected = cv2.cvtColor(corrected_lab, cv2.COLOR_LAB2BGR)
    return corrected


def enhance_contrast(image, clip_limit=2.0, tile_grid_size=(8, 8)):
    """
    Apply CLAHE (adaptive histogram equalization) on the L channel to
    improve local contrast without blowing out bright/dark regions.
    """
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    l_channel, a_channel, b_channel = cv2.split(lab)

    clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_grid_size)
    l_enhanced = clahe.apply(l_channel)

    enhanced_lab = cv2.merge((l_enhanced, a_channel, b_channel))
    enhanced = cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2BGR)
    return enhanced


def deskew_image(image, max_angle=15.0):
    """
    Estimate and correct small rotational skew (e.g. photo taken at a
    slight angle). Returns (deskewed_image, rotation_matrix_or_None).

    rotation_matrix is the 2x3 affine matrix passed to cv2.warpAffine.
    It is returned so callers can later invert it to map detected text
    coordinates back to this function's *input* coordinate frame.
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (5, 5), 0)

    _, thresh = cv2.threshold(
        gray, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU
    )

    coords = cv2.findNonZero(thresh)
    if coords is None or len(coords) < 50:
        # Not enough foreground pixels to estimate skew reliably.
        return image, None

    angle = cv2.minAreaRect(coords)[-1]

    # OpenCV's angle convention from minAreaRect is quirky across
    # versions; normalize it to a value in (-45, 45].
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle

    if abs(angle) < 0.3:
        # Negligible skew - don't bother rotating (avoids unnecessary
        # interpolation blur).
        return image, None

    if abs(angle) > max_angle:
        # Likely a bad estimate (e.g. dominated by a logo/graphic, not
        # text lines) - skip rather than risk rotating a fine image.
        return image, None

    (h, w) = image.shape[:2]
    center = (w / 2.0, h / 2.0)
    rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)

    rotated = cv2.warpAffine(
        image,
        rotation_matrix,
        (w, h),
        flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_REPLICATE,
    )
    return rotated, rotation_matrix


def sharpen_image(image, strength=1.0):
    """Simple unsharp mask to crisp up text edges before OCR."""
    blurred = cv2.GaussianBlur(image, (0, 0), 3)
    sharpened = cv2.addWeighted(image, 1 + strength, blurred, -strength, 0)
    return sharpened


# ------------------------------------------------------------------
# Full pipeline
# ------------------------------------------------------------------

def preprocess_pipeline(image, steps=None, cfg=None):
    """
    Run the enabled preprocessing steps in order and return
    (processed_image, transform).

    `image` is NEVER modified in place - we always start from a copy.
    `transform` records everything needed to map a coordinate from the
    final processed image back to the original image:
        {
            "scale_x": float,
            "scale_y": float,
            "rotation_matrix": 2x3 ndarray or None,
        }

    IMPORTANT ordering assumption: resize happens first (pure scale),
    deskew happens after (pure rotation, on the already-resized image).
    map_points_to_original() below assumes exactly this order when
    inverting the transform.
    """
    if steps is None:
        steps = {}

    working = image.copy()
    transform = identity_transform()

    if steps.get("resize", False):
        max_dim = getattr(cfg, "RESIZE_MAX_DIMENSION", None) if cfg else None
        working, scale_x, scale_y = resize_image(working, max_dim)
        transform["scale_x"] = scale_x
        transform["scale_y"] = scale_y

    if steps.get("glare_removal", False):
        threshold = getattr(cfg, "GLARE_BRIGHTNESS_THRESHOLD", 235) if cfg else 235
        working = remove_glare(working, threshold)

    if steps.get("illumination_correction", False):
        sigma = getattr(cfg, "ILLUMINATION_BLUR_SIGMA", 25) if cfg else 25
        working = correct_illumination(working, sigma)

    if steps.get("contrast_enhancement", False):
        clip_limit = getattr(cfg, "CLAHE_CLIP_LIMIT", 2.0) if cfg else 2.0
        tile_grid = getattr(cfg, "CLAHE_TILE_GRID_SIZE", (8, 8)) if cfg else (8, 8)
        working = enhance_contrast(working, clip_limit, tile_grid)

    if steps.get("deskew", False):
        max_angle = getattr(cfg, "DESKEW_MAX_ANGLE", 15.0) if cfg else 15.0
        working, rotation_matrix = deskew_image(working, max_angle)
        transform["rotation_matrix"] = rotation_matrix

    if steps.get("sharpen", False):
        strength = getattr(cfg, "SHARPEN_STRENGTH", 1.0) if cfg else 1.0
        working = sharpen_image(working, strength)

    return working, transform


# ------------------------------------------------------------------
# Coordinate mapping (processed image -> original image)
# ------------------------------------------------------------------

def map_points_to_original(points, transform):
    """
    Map a list of [x, y] points (e.g. a PaddleOCR polygon) detected in
    the processed image back to original-image coordinates.

    Order of inversion matches the pipeline order (resize then
    deskew): we first undo the rotation (getting back to the
    resized-but-not-rotated frame), then undo the scale.
    """
    pts = np.array(points, dtype=np.float32)

    orientation_matrix = transform.get("orientation_matrix")
    if orientation_matrix is not None:
        ones = np.ones((pts.shape[0], 1), dtype=np.float32)
        pts_homogeneous = np.hstack([pts, ones])
        pts = pts_homogeneous.dot(orientation_matrix.T)

    rotation_matrix = transform.get("rotation_matrix")
    if rotation_matrix is not None:
        inverse_matrix = cv2.invertAffineTransform(rotation_matrix)
        ones = np.ones((pts.shape[0], 1), dtype=np.float32)
        pts_homogeneous = np.hstack([pts, ones])
        pts = pts_homogeneous.dot(inverse_matrix.T)

    pts[:, 0] *= transform.get("scale_x", 1.0)
    pts[:, 1] *= transform.get("scale_y", 1.0)

    return pts


def rotate_orientation(image, angle):
    """Rotate by a quarter turn and return candidate-to-source mapping."""

    height, width = image.shape[:2]
    normalized_angle = angle % 360

    if normalized_angle == 0:
        matrix = np.array([[1, 0, 0], [0, 1, 0]], dtype=np.float32)
        return image.copy(), matrix

    if normalized_angle == 90:
        rotated = cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE)
        matrix = np.array(
            [[0, 1, 0], [-1, 0, height - 1]],
            dtype=np.float32
        )
        return rotated, matrix

    if normalized_angle == 180:
        rotated = cv2.rotate(image, cv2.ROTATE_180)
        matrix = np.array(
            [[-1, 0, width - 1], [0, -1, height - 1]],
            dtype=np.float32
        )
        return rotated, matrix

    if normalized_angle == 270:
        rotated = cv2.rotate(image, cv2.ROTATE_90_COUNTERCLOCKWISE)
        matrix = np.array(
            [[0, -1, width - 1], [1, 0, 0]],
            dtype=np.float32
        )
        return rotated, matrix

    raise ValueError("Orientation angle must be one of 0, 90, 180, or 270")
