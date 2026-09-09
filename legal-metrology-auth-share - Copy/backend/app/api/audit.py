from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.audit import AuditLog
from app.db.database import get_db
from app.db.models import UserModel
from app.dependencies import require_admin


router = APIRouter(
    prefix="/audit",
    tags=["Audit Logs"],
)


@router.get("/logs")
def get_audit_logs(
    current_user: UserModel = Depends(require_admin),
    db: Session = Depends(get_db),
):
    logs = (
        db.query(AuditLog)
        .order_by(AuditLog.created_at.desc())
        .limit(200)
        .all()
    )

    return [
        {
            "id": log.id,
            "user_id": log.user_id,
            "action": log.action,
            "resource": log.resource,
            "details": log.details,
            "ip_address": log.ip_address,
            "created_at": log.created_at,
        }
        for log in logs
    ]