from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.config import settings
from app.db.audit import create_audit_log
from app.db.database import get_db
from app.db.models import UserModel
from app.dependencies import get_current_user
from app.security import create_access_token, hash_password, verify_password


router = APIRouter(prefix="/auth", tags=["Authentication"])


def is_government_email(email: str) -> bool:
    domain = email.lower().split("@")[-1]

    allowed_domains = {
        d.strip().lower()
        for d in settings.government_email_domains.split(",")
        if d.strip()
    }

    return domain in allowed_domains


class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: str
    is_active: bool


class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED
)
def register(
    request: Request,
    data: RegisterRequest,
    db: Session = Depends(get_db)
):
    existing_user = (
        db.query(UserModel)
        .filter(UserModel.email == data.email)
        .first()
    )

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )

    if len(data.password) < 8:
        raise HTTPException(
            status_code=400,
            detail="Password must be at least 8 characters"
        )

    # Government-domain users automatically become Inspectors.
    # All other users become Citizens.
    user_role = (
        "inspector"
        if is_government_email(data.email)
        else "citizen"
    )

    user = UserModel(
        name=data.name,
        email=data.email,
        password_hash=hash_password(data.password),
        role=user_role,
        is_active=True
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    create_audit_log(
        db=db,
        user_id=user.id,
        action="REGISTER",
        resource="authentication",
        details=f"New {user_role} account created",
        ip_address=request.client.host if request.client else None
    )

    return user


@router.post("/login", response_model=LoginResponse)
def login(
    request: Request,
    data: LoginRequest,
    db: Session = Depends(get_db)
):
    user = (
        db.query(UserModel)
        .filter(UserModel.email == data.email)
        .first()
    )

    if user is None or not verify_password(
        data.password,
        user.password_hash
    ):
        create_audit_log(
            db=db,
            action="LOGIN_FAILED",
            resource="authentication",
            details="Failed login attempt",
            ip_address=request.client.host if request.client else None
        )

        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    if not user.is_active:
        create_audit_log(
            db=db,
            user_id=user.id,
            action="LOGIN_BLOCKED",
            resource="authentication",
            details="Login attempted on inactive account",
            ip_address=request.client.host if request.client else None
        )

        raise HTTPException(
            status_code=403,
            detail="User account is inactive"
        )

    token = create_access_token(
        user_id=user.id,
        role=user.role
    )

    create_audit_log(
        db=db,
        user_id=user.id,
        action="LOGIN",
        resource="authentication",
        details="Successful login",
        ip_address=request.client.host if request.client else None
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user
    }


@router.post("/token")
def token_login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = (
        db.query(UserModel)
        .filter(UserModel.email == form_data.username)
        .first()
    )

    if user is None or not verify_password(
        form_data.password,
        user.password_hash
    ):
        create_audit_log(
            db=db,
            action="LOGIN_FAILED",
            resource="authentication",
            details="Failed OAuth2 login attempt",
            ip_address=request.client.host if request.client else None
        )

        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"}
        )

    if not user.is_active:
        raise HTTPException(
            status_code=403,
            detail="User account is inactive"
        )

    access_token = create_access_token(
        user_id=user.id,
        role=user.role
    )

    create_audit_log(
        db=db,
        user_id=user.id,
        action="LOGIN",
        resource="authentication",
        details="Successful OAuth2 login",
        ip_address=request.client.host if request.client else None
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


@router.post("/change-password")
def change_password(
    request: Request,
    data: ChangePasswordRequest,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not verify_password(
        data.current_password,
        current_user.password_hash
    ):
        create_audit_log(
            db=db,
            user_id=current_user.id,
            action="PASSWORD_CHANGE_FAILED",
            resource="authentication",
            details="Incorrect current password",
            ip_address=request.client.host if request.client else None
        )

        raise HTTPException(
            status_code=400,
            detail="Current password is incorrect"
        )

    if len(data.new_password) < 8:
        raise HTTPException(
            status_code=400,
            detail="New password must be at least 8 characters"
        )

    if data.current_password == data.new_password:
        raise HTTPException(
            status_code=400,
            detail="New password must be different"
        )

    current_user.password_hash = hash_password(
        data.new_password
    )

    db.commit()

    create_audit_log(
        db=db,
        user_id=current_user.id,
        action="PASSWORD_CHANGED",
        resource="authentication",
        details="User changed password",
        ip_address=request.client.host if request.client else None
    )

    return {
        "message": "Password changed successfully"
    }