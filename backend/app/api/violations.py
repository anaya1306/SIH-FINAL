from fastapi import APIRouter, HTTPException, Query

from app.schemas.violation import ViolationListResponse
from app.services.store import store

router = APIRouter(tags=["violations"])


@router.get("/scans/{scan_id}/violations", response_model=ViolationListResponse)
def get_scan_violations(scan_id: str) -> ViolationListResponse:
    scan = store.get_scan(scan_id)
    if not scan:
        raise HTTPException(status_code=404, detail=f"Scan {scan_id} not found")
    return ViolationListResponse(items=scan.violations, total=len(scan.violations), scan_id=scan_id)


@router.get("/violations", response_model=ViolationListResponse)
def list_violations(scan_id: str | None = Query(default=None)) -> ViolationListResponse:
    items = store.list_violations(scan_id)
    return ViolationListResponse(items=items, total=len(items), scan_id=scan_id)
