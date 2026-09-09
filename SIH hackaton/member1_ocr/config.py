"""
config.py
---------
Central configuration for Member 1's OCR module.

Nothing in this file talks to PaddleOCR or OpenCV directly - it's just
tunable constants so preprocessing.py and ocr_engine.py stay simple and
easy to change without hunting through code.
"""
from pathlib import Path
# ============================================================
# OCR ENGINE CONFIG
# ============================================================


OCR_LANG = "en"          # PaddleOCR language model to load
USE_ANGLE_CLS = False     # keep OCR fast for the prototype; angle-classification is slow
USE_GPU = False           # set True only if paddlepaddle-gpu is installed

# For the PackScan workflow, the app is typically processing real package
# photos, so we avoid the expensive multi-angle OCR search and run on the
# already preprocessed image to keep response times reasonable.
USE_ORIENTATION_SEARCH = False
ORIENTATION_ANGLES = (0,)

# Whether OCR should run on the preprocessed image or the raw original.
# True is recommended for real package photos (glare, poor light, skew).
# Both paths are always supported - see ocr_engine.run_ocr(use_preprocessed=...)
USE_PREPROCESSED_IMAGE = True

# NOTE: this threshold is NOT used to delete or hide OCR results.
# Low-confidence text is still returned as-is (per project requirements).
# It is only exposed here so callers/UI/analytics can flag "low confidence"
# text if they want to, without touching ocr_engine.py.
OCR_CONFIDENCE_THRESHOLD = 0.5

# ============================================================
# PREPROCESSING CONFIG
# ============================================================

# Toggle individual preprocessing stages on/off.
PREPROCESS_STEPS = {
    "resize": True,
    "glare_removal": False,
    "illumination_correction": False,
    "contrast_enhancement": True,
    "deskew": False,
    "sharpen": False,
}

# Resize: the longest side of the image is scaled down to this many pixels
# (aspect ratio preserved). Set to None to disable resizing even if
# PREPROCESS_STEPS["resize"] is True. Large phone photos (3000-4000px) slow
# PaddleOCR down a lot without much accuracy gain, so we cap it.
RESIZE_MAX_DIMENSION = 1200

# Glare removal: pixels brighter than this (0-255, grayscale) are treated
# as glare/hotspots and inpainted.
GLARE_BRIGHTNESS_THRESHOLD = 235

# Illumination correction: sigma of the Gaussian used to estimate the
# background lighting, which is then divided out.
ILLUMINATION_BLUR_SIGMA = 25

# CLAHE (contrast enhancement) params.
CLAHE_CLIP_LIMIT = 2.0
CLAHE_TILE_GRID_SIZE = (8, 8)

# Deskew: if the detected skew angle is larger than this (degrees), we
# assume detection failed (or the image is intentionally rotated a lot)
# and skip correction rather than risk making things worse.
DESKEW_MAX_ANGLE = 15.0

# Sharpen (unsharp mask) strength. Higher = stronger sharpening.
SHARPEN_STRENGTH = 1.0

# ============================================================
# OUTPUT CONFIG
# ============================================================

DEFAULT_OUTPUT_JSON = str(
    Path(__file__).resolve().parent / "ocr_output.json"
)
