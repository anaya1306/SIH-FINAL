# Member 1 Module — Computer Vision + OCR

Software System to check compliance of Packaged Commodities under Legal
Metrology (Packaged Commodities) Rules, 2011 — **SIH prototype**.

This module is **only** responsible for:

```
Product Image → Preprocessing → PaddleOCR → Regions + Confidence → Standard JSON
```

It does **not** do field extraction, text correction, or Legal Metrology
rule checking — that's Member 2's job, and it consumes the JSON this
module produces.

---

## 1. Folder structure

```
member1_ocr/
│
├── config.py          # all tunable settings (thresholds, sizes, toggles)
├── preprocessing.py    # modular image preprocessing + coordinate mapping
├── ocr_engine.py        # PaddleOCR init/execution + standardized JSON output
├── test_ocr.py           # CLI test script
├── requirements.txt
└── README.md
```

- `preprocessing.py` never imports PaddleOCR — it's pure OpenCV/NumPy.
- `ocr_engine.py` is the only file that talks to PaddleOCR.
- `test_ocr.py` only calls `ocr_engine.run_ocr()` — it never touches
  PaddleOCR or OpenCV directly.

---

## 2. Installation

```bash
cd member1_ocr
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt
```

> **Note:** `paddleocr` will download detection/recognition model
> weights (a few hundred MB) the first time you run it. Make sure
> there's internet access the first time.

If you have a CUDA-capable GPU and want faster inference:

```bash
pip uninstall paddlepaddle
pip install paddlepaddle-gpu==2.6.1
```

then set `USE_GPU = True` in `config.py`.

---

## 3. Running the OCR

```bash
python test_ocr.py sample.jpg
```

Optional flags:

```bash
# Run OCR on the raw original image, skipping preprocessing entirely
python test_ocr.py sample.jpg --original

# Save output to a custom file instead of ocr_output.json
python test_ocr.py sample.jpg --out my_result.json
```

This will:

1. Load `sample.jpg`
2. Run the preprocessing pipeline (resize → glare removal →
   illumination correction → contrast enhancement → deskew → sharpen)
3. Run PaddleOCR on the (pre)processed image
4. Map every detected bounding box back to **original image
   coordinates**
5. Print the standardized JSON to the terminal
6. Save it to `ocr_output.json` (or `--out` path)

---

## 4. JSON output contract

```json
{
  "engine": "paddle",
  "image_size": {
    "width": 3024,
    "height": 4032
  },
  "regions": [
    {
      "text": "Mfg.ByNestle India Limited",
      "bbox": { "x": 153, "y": 2534, "width": 947, "height": 190 },
      "confidence": 0.9282
    },
    {
      "text": "OWECARE@WNEE.COM",
      "bbox": { "x": 210, "y": 2810, "width": 610, "height": 60 },
      "confidence": 0.6143
    }
  ],
  "full_text": "MRP ₹15.00\n250 g\nMfg.ByNestle India Limited\nOWECARE@WNEE.COM"
}
```

On failure (bad path, unreadable file, engine crash), the module
returns instead of raising:

```json
{ "error": "Image not found: sample.jpg", "engine": "paddle" }
```

If OCR runs successfully but detects nothing, it returns empty
`regions`/`full_text` plus a `warning` field — never an exception:

```json
{
  "engine": "paddle",
  "image_size": { "width": 1200, "height": 900 },
  "regions": [],
  "full_text": "",
  "warning": "No text detected in image."
}
```

**Guarantees:**

- Every region always has `text`, `bbox`, and `confidence`.
- `bbox` is always `{x, y, width, height}` in **original image**
  pixel coordinates — even when OCR internally ran on a resized/
  deskewed version of the image.
- Text is **never** manually corrected. Whatever PaddleOCR outputs
  (typos, garbled characters, merged words) is returned as-is.
  Low-confidence results are **not** deleted — `confidence` is always
  included so Member 2/the rules engine can decide what to do with it.

---

## 5. How coordinate mapping works

Two preprocessing steps change image geometry: **resize** (pure scale)
and **deskew** (pure rotation). Both are tracked in a small `transform`
dict:

```python
{"scale_x": 1.51, "scale_y": 1.51, "rotation_matrix": <2x3 array or None>}
```

When a text region is detected in the processed image,
`preprocessing.map_points_to_original()`:

1. Inverts the rotation matrix (if deskew ran) to undo rotation.
2. Multiplies by `scale_x` / `scale_y` to undo resizing.

This gives back the polygon in the original image's coordinate space,
which is then converted to an axis-aligned `x, y, width, height` box.

If you disable a step in `config.PREPROCESS_STEPS`, or run with
`--original` / `use_preprocessed=False`, the transform is just the
identity (`scale=1, rotation=None`) and OCR runs directly on the
original pixels.

---

## 6. How Member 2 should consume the output

Member 2's extractor should call:

```python
import ocr_engine

result = ocr_engine.run_ocr("sample.jpg")

if "error" in result:
    # handle gracefully - e.g. ask user to re-upload / re-photograph
    ...
else:
    full_text = result["full_text"]   # for field extraction (regex/NLP)
    regions = result["regions"]        # for evidence mapping / highlighting
```

- **`full_text`** — a single newline-joined string in a reasonable
  top-to-bottom, left-to-right reading order. Use this for extracting
  product name, generic name, net quantity, MRP, manufacturer,
  address, batch number, mfg/use-by dates, consumer care phone/email,
  etc.
- **`regions`** — use this to map an extracted field back to *where*
  it was found on the label (for highlighting evidence in a UI, or for
  cross-checking that e.g. "MRP" text and its bounding box are close
  to a "₹" symbol region).

Member 2 should **not** assume text is clean — raw OCR artifacts
(merged words, missing spaces, wrong characters) are expected and are
Member 2's problem to normalize.

Overall architecture:

```
IMAGE
 ↓
MEMBER 1 OCR  (this module)
 ↓
{ regions: [{text, bbox, confidence}], full_text }
 ↓
MEMBER 2 EXTRACTOR
 ↓
STRUCTURED FIELDS
 ↓
LEGAL METROLOGY RULE ENGINE
```

---

## 7. Common errors & fixes

| Error | Cause | Fix |
|---|---|---|
| `Image not found: <path>` | Wrong path / typo / relative path issue | Double check the path, use an absolute path if unsure |
| `Could not read image (corrupt, unsupported format...)` | File isn't a valid image, or is a format OpenCV can't decode (e.g. HEIC) | Convert to JPG/PNG first, or verify the file isn't 0 bytes / corrupted |
| `paddleocr is not installed` | Dependencies not installed / wrong venv active | `pip install -r requirements.txt`, confirm you activated the venv |
| First run hangs / is very slow | PaddleOCR is downloading model weights | Wait it out once; it's cached under `~/.paddleocr` afterward |
| `OCR engine failure: ...` | Corrupt image data reaching Paddle, out-of-memory on huge images, or a Paddle/OpenCV version mismatch | Lower `RESIZE_MAX_DIMENSION` in `config.py`, verify `requirements.txt` versions match, re-run with `--original` to isolate whether preprocessing is the cause |
| `regions: []` with a `warning` | Genuinely no readable text (blurry photo, blank label) or text too small/rotated | Retake photo closer/straighter, try `--original` vs preprocessed to compare, increase `RESIZE_MAX_DIMENSION` |
| Bounding boxes look "off"/shifted | Should not happen with default config, but if you add a new preprocessing step that changes geometry (e.g. cropping) without updating the `transform` dict in `preprocess_pipeline()`, coordinates will be wrong | Any new geometry-changing step **must** update `scale_x`/`scale_y`/`rotation_matrix` (or add a new transform component and account for it in `map_points_to_original`) |
| Slow on CPU | Normal — PaddleOCR on CPU is not fast, especially on large images | Lower `RESIZE_MAX_DIMENSION`, or switch to GPU (`paddlepaddle-gpu`, `USE_GPU=True`) |

---

## 8. Pre-flight checklist (already verified for this build)

- [x] `bbox` is always in **original image** coordinates, for both the
      preprocessed and `--original` code paths.
- [x] Every region has `text` + `bbox` + `confidence`.
- [x] `full_text` is always present (empty string if nothing detected).
- [x] Raw OCR text is never rewritten/"corrected" anywhere in this module.
- [x] All return values are plain dicts of JSON-serializable types
      (`json.dumps(result, indent=2)` always works).
- [x] `run_ocr()` never raises for expected failure modes (bad path,
      bad image, empty OCR result, engine crash) — it returns an
      `{"error": ...}` dict instead, so Member 2 can integrate it
      directly without wrapping every call in try/except.
