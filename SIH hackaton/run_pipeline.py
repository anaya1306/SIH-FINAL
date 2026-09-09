import subprocess
import sys
from pathlib import Path


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent

MEMBER1_DIR = PROJECT_ROOT / "member1_ocr"
MEMBER2_DIR = PROJECT_ROOT / "member 2"
MEMBER6_DIR = PROJECT_ROOT / "member_6"


# ============================================================
# HELPER
# ============================================================

def run_step(name, command, cwd):
    print("\n" + "=" * 70)
    print(f"RUNNING: {name}")
    print("=" * 70)

    result = subprocess.run(
        command,
        cwd=str(cwd),
        check=False
    )

    if result.returncode != 0:
        print("\n" + "=" * 70)
        print(f"FAILED: {name}")
        print("=" * 70)
        sys.exit(result.returncode)

    print("\n" + "=" * 70)
    print(f"COMPLETED: {name}")
    print("=" * 70)


# ============================================================
# MAIN PIPELINE
# ============================================================

def main():

    print("\n")
    print("=" * 70)
    print(" PACKAGED COMMODITY COMPLIANCE PIPELINE")
    print("=" * 70)

    # --------------------------------------------------------
    # STEP 1
    # Member 1 - OCR
    # --------------------------------------------------------

    run_step(
        "MEMBER 1 - OCR",
        [
            sys.executable,
            "test_ocr.py",
        ],
        MEMBER1_DIR,
    )

    # --------------------------------------------------------
    # Verify OCR output
    # --------------------------------------------------------

    ocr_output = MEMBER1_DIR / "ocr_output.json"

    if not ocr_output.exists():

        print(
            "\nERROR: Member 1 did not generate "
            "ocr_output.json"
        )

        sys.exit(1)

    print(
        f"\nOCR output found:\n{ocr_output}"
    )

    # --------------------------------------------------------
    # STEP 2
    # Member 2 - Extraction + Rules Engine
    # --------------------------------------------------------

    run_step(
        "MEMBER 2 - EXTRACTION + RULES",
        [
            sys.executable,
            "pipeline_test.py",
        ],
        MEMBER2_DIR,
    )

    # --------------------------------------------------------
    # Verify Member 2 output
    # --------------------------------------------------------

    final_output = MEMBER2_DIR / "final_output.json"

    if not final_output.exists():

        print(
            "\nERROR: Member 2 did not generate "
            "final_output.json"
        )

        sys.exit(1)

    print(
        f"\nMember 2 output found:\n{final_output}"
    )

    # --------------------------------------------------------
    # STEP 3
    # Member 6 - PDF Report
    # --------------------------------------------------------

    run_step(
        "MEMBER 6 - PDF REPORT",
        [
            sys.executable,
            "pdf_generator.py",
        ],
        MEMBER6_DIR,
    )

    # --------------------------------------------------------
    # Verify PDF
    # --------------------------------------------------------

    pdf_output = MEMBER6_DIR / "inspection_report.pdf"

    if not pdf_output.exists():

        print(
            "\nERROR: Member 6 did not generate "
            "inspection_report.pdf"
        )

        sys.exit(1)

    print("\n")
    print("=" * 70)
    print(" PIPELINE COMPLETED SUCCESSFULLY")
    print("=" * 70)

    print("\nGenerated files:")

    print(
        f"\n1. OCR JSON:"
        f"\n   {ocr_output}"
    )

    print(
        f"\n2. Compliance JSON:"
        f"\n   {final_output}"
    )

    print(
        f"\n3. Inspection PDF:"
        f"\n   {pdf_output}"
    )

    print("\n" + "=" * 70)


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()