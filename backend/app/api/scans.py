import asyncio
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status

from app.schemas.field import ExtractRequest, ExtractResponse
from app.schemas.scan import ScanCreate, ScanDetailResponse, ScanListResponse, ScanResponse, ScanStatus
from app.services.extraction import check_violations, extract_fields_from_text, utc_now
from app.services.ocr_client import call_ocr_api, call_ocr_api_sync
from app.services.pipeline import get_pipeline_analysis
from app.services.store import store

router = APIRouter(prefix="/scans", tags=["scans"])


def _to_scan_response(scan) -> ScanResponse:
    return ScanResponse(
        id=scan.id,
        status=scan.status,
        product_name=scan.product_name,
        image_url=scan.image_url,
        created_at=scan.created_at,
    )


def _to_scan_detail(scan) -> ScanDetailResponse:
    return ScanDetailResponse(
        id=scan.id,
        status=scan.status,
        product_name=scan.product_name,
        image_url=scan.image_url,
        created_at=scan.created_at,
        compliance_score=scan.compliance_score,
        fields=scan.fields,
        violations=scan.violations,
    )


@router.post("", response_model=ScanResponse, status_code=status.HTTP_201_CREATED)
def create_scan(payload: ScanCreate) -> ScanResponse:
    scan = store.create_scan(
        product_name=payload.product_name,
        image_url=payload.image_url,
        raw_ocr_text=payload.raw_ocr_text,
    )
    scan.created_at = utc_now()
    return _to_scan_response(scan)


@router.get("", response_model=ScanListResponse)
def list_scans() -> ScanListResponse:
    items = [_to_scan_response(s) for s in store.list_scans()]
    return ScanListResponse(items=items, total=len(items))


@router.get("/demo")
async def demo_pipeline_analysis(product_name: str = "Parle-G", image_url: str | None = None) -> dict:
    analysis = await asyncio.to_thread(get_pipeline_analysis, product_name=product_name, image_url=image_url)

    scan = store.create_scan(
        product_name=analysis["product_name"],
        image_url=analysis.get("image_url"),
        raw_ocr_text=analysis.get("raw_ocr_text"),
    )
    scan.created_at = utc_now()

    store.update_scan_fields(scan.id, analysis.get("fields", []), analysis.get("violations", []))

    return {
        "scan_id": scan.id,
        "product_name": scan.product_name,
        "image_url": scan.image_url,
        "raw_ocr_text": scan.raw_ocr_text,
        "fields": scan.fields,
        "violations": scan.violations,
        "compliance_score": scan.compliance_score,
        "overall_status": analysis.get("overall_status", "NEEDS_REVIEW"),
        "pdf_path": analysis.get("pdf_path"),
        "engine": analysis.get("engine"),
        "created_at": scan.created_at,
    }


@router.post("/analyze")
async def analyze_uploaded_scan(
    file: UploadFile = File(...),
    product_name: str = Form("Uploaded Product"),
) -> dict:
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    suffix = Path(file.filename).suffix or ".jpg"
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as handle:
            handle.write(contents)
            tmp_path = handle.name

        analysis = await asyncio.to_thread(
            get_pipeline_analysis,
            product_name=product_name,
            image_url=file.filename,
            uploaded_image_path=tmp_path,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Unable to analyze uploaded image: {exc}") from exc
    finally:
        if tmp_path:
            try:
                Path(tmp_path).unlink(missing_ok=True)
            except Exception:
                pass

    scan = store.create_scan(
        product_name=analysis["product_name"],
        image_url=analysis.get("image_url"),
        raw_ocr_text=analysis.get("raw_ocr_text"),
    )
    scan.created_at = utc_now()
    store.update_scan_fields(scan.id, analysis.get("fields", []), analysis.get("violations", []))

    return {
        "scan_id": scan.id,
        "product_name": scan.product_name,
        "image_url": scan.image_url,
        "raw_ocr_text": scan.raw_ocr_text,
        "fields": scan.fields,
        "violations": scan.violations,
        "compliance_score": scan.compliance_score,
        "overall_status": analysis.get("overall_status", "NEEDS_REVIEW"),
        "pdf_path": analysis.get("pdf_path"),
        "engine": analysis.get("engine"),
        "created_at": scan.created_at,
    }


@router.get("/{scan_id}", response_model=ScanDetailResponse)
def get_scan(scan_id: str) -> ScanDetailResponse:
    scan = store.get_scan(scan_id)
    if not scan:
        raise HTTPException(status_code=404, detail=f"Scan {scan_id} not found")
    return _to_scan_detail(scan)


@router.post("/ocr-extract")
async def ocr_extract(
    file: UploadFile = File(...),
    product_name: str = Form("Uploaded Product"),
    mode: str = Form("citizen"),
    engine: str = Form("auto"),
) -> dict:
    """Direct OCR + extraction using packaging-ocr API."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    try:
        ocr_result = await call_ocr_api(contents, mode=mode, engine=engine)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"OCR API error: {exc}") from exc

    full_text = ocr_result.get("full_text", "")
    extracted = ocr_result.get("extracted", {})

    fields = extract_fields_from_text(full_text)
    violations = check_violations("temp-scan", fields, full_text)

    scan = store.create_scan(
        product_name=product_name,
        image_url=file.filename,
        raw_ocr_text=full_text,
    )
    scan.created_at = utc_now()
    store.update_scan_fields(scan.id, fields, violations)

    return {
        "scan_id": scan.id,
        "product_name": product_name,
        "ocr_text": full_text,
        "extracted_fields": extracted,
        "fields": fields,
        "violations": violations,
        "engine": ocr_result.get("engine"),
        "mean_confidence": ocr_result.get("mean_confidence"),
    }


@router.post("/{scan_id}/extract", response_model=ExtractResponse)
def extract_fields(scan_id: str, payload: ExtractRequest) -> ExtractResponse:
    scan = store.get_scan(scan_id)
    if not scan:
        raise HTTPException(status_code=404, detail=f"Scan {scan_id} not found")

    fields = extract_fields_from_text(payload.raw_ocr_text)
    violations = check_violations(scan_id, fields, payload.raw_ocr_text)
    scan.raw_ocr_text = payload.raw_ocr_text
    store.update_scan_fields(scan_id, fields, violations)

    return ExtractResponse(
        scan_id=scan_id,
        fields=fields,
        extracted_at=datetime.now(timezone.utc),
    )
