"""
test_ocr.py

Simple CLI test harness for Member 1's OCR module.

Usage:
    python test_ocr.py sample.jpg
    python test_ocr.py sample.jpg --original
    python test_ocr.py sample.jpg --out result.json
"""

import sys
import json
import config
import ocr_engine


def _parse_args(argv):
    if len(argv) < 1:
        print("Usage: python test_ocr.py <image_path> [--original] [--out FILE]")
        sys.exit(1)

    image_path = argv[0]

    # Use config.py as the default.
    # --original always forces raw/original image.
    use_preprocessed = config.USE_PREPROCESSED_IMAGE

    if "--original" in argv:
        use_preprocessed = False

    output_path = config.DEFAULT_OUTPUT_JSON

    if "--out" in argv:
        idx = argv.index("--out")

        if idx + 1 < len(argv):
            output_path = argv[idx + 1]

    return image_path, use_preprocessed, output_path


def main():
    image_path, use_preprocessed, output_path = _parse_args(sys.argv[1:])

    print(f"Image path        : {image_path}")
    print(f"Use preprocessing : {use_preprocessed}")
    print("Running OCR...\n")

    result = ocr_engine.run_ocr(
        image_path,
        use_preprocessed=use_preprocessed
    )

    output_json = json.dumps(
        result,
        indent=2,
        ensure_ascii=False
    )

    print(output_json)

    if "error" in result:
        print("\nOCR failed - see 'error' field above. No output file written.")
        sys.exit(1)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(output_json)

    region_count = len(result.get("regions", []))

    print(f"\nDetected {region_count} text region(s).")
    print(f"Saved JSON output to: {output_path}")


if __name__ == "__main__":
    main()