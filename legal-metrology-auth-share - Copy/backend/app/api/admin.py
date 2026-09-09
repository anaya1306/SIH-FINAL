import os

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.config import settings
from app.db.audit import create_audit_log
from app.db.database import get_db
from app.db.models import UserModel
from app.dependencies import require_admin

router = APIRouter(prefix="/admin", tags=["Admin"])


def get_admin_emails():
    return {
        email.strip().lower()
        for email in settings.admin_emails.split(",")
        if email.strip()
    }


@router.get("/users")
def get_users(
    current_user: UserModel = Depends(require_admin),
    db: Session = Depends(get_db)
):
    users = db.query(UserModel).all()

    return [
        {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role,
            "is_active": user.is_active,
            "created_at": user.created_at,
        }
        for user in users
    ]


@router.put("/users/{user_id}/role")
def change_user_role(
    user_id: int,
    role: str,
    current_user: UserModel = Depends(require_admin),
    db: Session = Depends(get_db)
):
    role = role.strip().lower()

    if role not in {"citizen", "inspector", "admin"}:
        raise HTTPException(
            status_code=400,
            detail="Role must be citizen, inspector or admin"
        )

    user = db.query(UserModel).filter(UserModel.id == user_id).first()

    if user is None:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    if user.id == current_user.id and role != "admin":
        raise HTTPException(
            status_code=400,
            detail="Admin cannot remove their own admin role"
        )

    if role == "admin":
        allowed_admins = get_admin_emails()

        if user.email.lower() not in allowed_admins:
            raise HTTPException(
                status_code=400,
                detail="This email is not authorized to be an admin"
            )

    old_role = user.role
    user.role = role

    db.commit()
    db.refresh(user)

    create_audit_log(
        db=db,
        user_id=current_user.id,
        action="ROLE_CHANGED",
        resource="user",
        details=f"User {user.email}: {old_role} -> {role}"
    )

    return {
        "message": "User role updated successfully",
        "user_id": user.id,
        "email": user.email,
        "old_role": old_role,
        "new_role": user.role
    }


@router.put("/users/{user_id}/status")
def change_user_status(
    user_id: int,
    is_active: bool,
    current_user: UserModel = Depends(require_admin),
    db: Session = Depends(get_db)
):
    user = db.query(UserModel).filter(UserModel.id == user_id).first()

    if user is None:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    if user.id == current_user.id and not is_active:
        raise HTTPException(
            status_code=400,
            detail="Admin cannot deactivate their own account"
        )

    old_status = user.is_active
    user.is_active = is_active

    db.commit()
    db.refresh(user)

    create_audit_log(
        db=db,
        user_id=current_user.id,
        action="ACCOUNT_STATUS_CHANGED",
        resource="user",
        details=f"User {user.email}: {old_status} -> {is_active}"
    )

    return {
        "message": "User status updated successfully",
        "user_id": user.id,
        "email": user.email,
        "is_active": user.is_active
    }