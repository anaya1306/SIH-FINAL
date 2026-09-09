from fastapi import APIRouter, Depends

from app.db.models import UserModel
from app.dependencies import (
    get_current_user,
    require_admin,
    require_inspector,
)


router = APIRouter(
    prefix="/rbac",
    tags=["RBAC"]
)


@router.get("/citizen")
def citizen_access(
    current_user: UserModel = Depends(get_current_user),
):
    return {
        "message": "Citizen access granted",
        "user": current_user.email,
        "role": current_user.role,
    }


@router.get("/inspector")
def inspector_access(
    current_user: UserModel = Depends(require_inspector),
):
    return {
        "message": "Inspector access granted",
        "user": current_user.email,
        "role": current_user.role,
    }


@router.get("/admin")
def admin_access(
    current_user: UserModel = Depends(require_admin),
):
    return {
        "message": "Admin access granted",
        "user": current_user.email,
        "role": current_user.role,
    }