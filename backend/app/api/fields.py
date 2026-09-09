from fastapi import APIRouter, HTTPException

from app.schemas.field import ExtractedField
from app.services.store import store

router = APIRouter(prefix="/scans", tags=["fields"])


@router.get("/{scan_id}/fields", response_model=list[ExtractedField])
def get_scan_fields(scan_id: str) -> list[ExtractedField]:
    scan = store.get_scan(scan_id)
    if not scan:
        raise HTTPException(status_code=404, detail=f"Scan {scan_id} not found")
    return scan.fields
