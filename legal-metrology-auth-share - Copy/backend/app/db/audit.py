from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, Session, mapped_column

from app.db.database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    user_id: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True
    )

    action: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    resource: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )

    details: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    ip_address: Mapped[str | None] = mapped_column(
        String(45),
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )


def create_audit_log(
    db: Session,
    action: str,
    user_id: int | None = None,
    resource: str | None = None,
    details: str | None = None,
    ip_address: str | None = None,
) -> AuditLog:
    log = AuditLog(
        user_id=user_id,
        action=action,
        resource=resource,
        details=details,
        ip_address=ip_address,
    )

    db.add(log)
    db.commit()
    db.refresh(log)

    return log