import jwt

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import UserModel
from app.security import decode_access_token


oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/token"
)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> UserModel:

    try:
        payload = decode_access_token(token)

        user_id = int(payload["sub"])

    except (
        jwt.InvalidTokenError,
        KeyError,
        ValueError,
        TypeError,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = (
        db.query(UserModel)
        .filter(UserModel.id == user_id)
        .first()
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    return user


def require_inspector(
    current_user: UserModel = Depends(get_current_user),
) -> UserModel:

    if current_user.role not in {"inspector", "admin"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inspector access required",
        )

    return current_user


def require_admin(
    current_user: UserModel = Depends(get_current_user),
) -> UserModel:

    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )

    return current_user