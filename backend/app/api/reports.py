from fastapi import APIRouter, HTTPException, status

from app.schemas.report import ReportDetail, ReportListResponse, ReportSummary
from app.services.store import store

router = APIRouter(prefix="/reports", tags=["reports"])


@router.post("/{scan_id}", response_model=ReportDetail, status_code=status.HTTP_201_CREATED)
def generate_report(scan_id: str) -> ReportDetail:
    """
    Generate a compliance report for a scan.
    
    - **scan_id**: The ID of the scan to generate a report for
    
    Returns detailed compliance report with fields, violations, recommendations.
    """
    scan = store.get_scan(scan_id)
    if not scan:
        raise HTTPException(status_code=404, detail=f"Scan {scan_id} not found")
    
    return store.generate_report(scan_id)


@router.get("", response_model=ReportListResponse)
def list_reports() -> ReportListResponse:
    """
    List all generated compliance reports.
    
    Returns a paginated list of report summaries sorted by generation date.
    """
    items = [
        ReportSummary(
            id=r.id,
            scan_id=r.scan_id,
            product_name=r.product_name,
            compliance_score=r.compliance_score,
            violation_count=r.violation_count,
            status=r.status,
            generated_at=r.generated_at,
        )
        for r in store.list_reports()
    ]
    return ReportListResponse(items=items, total=len(items))


@router.get("/{report_id}", response_model=ReportDetail)
def get_report(report_id: str) -> ReportDetail:
    """
    Fetch a specific compliance report by ID.
    
    - **report_id**: The ID of the report to retrieve
    
    Returns the full report details including violations and recommendations.
    """
    report = store.get_report(report_id)
    if not report:
        raise HTTPException(status_code=404, detail=f"Report {report_id} not found")
    
    scan = store.get_scan(report.scan_id)
    if not scan:
        raise HTTPException(status_code=404, detail=f"Associated scan not found")
    
    return ReportDetail(
        id=report.id,
        scan_id=report.scan_id,
        product_name=report.product_name,
        compliance_score=report.compliance_score,
        violation_count=report.violation_count,
        status=report.status,
        generated_at=report.generated_at,
        fields=scan.fields,
        violations=scan.violations,
        inspector_notes=report.inspector_notes,
        recommendations=report.recommendations,
    )
