from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel

from app.services.auth import authenticate_user, create_token, register_user, verify_token

router = APIRouter(tags=["auth"])


class LoginRequest(BaseModel):
    email: str
    password: str
    role: str | None = None


class LoginResponse(BaseModel):
    token: str
    user: dict[str, str]


class SignupRequest(BaseModel):
    name: str
    email: str
    password: str
    phone: str | None = None
    role: str | None = None


@router.post("/auth/login", response_model=LoginResponse, status_code=status.HTTP_200_OK)
def login(payload: LoginRequest) -> LoginResponse:
    user = authenticate_user(payload.email, payload.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if payload.role and user["role"] != payload.role:
        user = {**user, "role": payload.role}

    token = create_token(user)
    return LoginResponse(token=token, user=user)


@router.post("/auth/signup", response_model=LoginResponse, status_code=status.HTTP_201_CREATED)
def signup(payload: SignupRequest) -> LoginResponse:
    try:
        user = register_user(
            name=payload.name,
            email=payload.email,
            password=payload.password,
            phone=payload.phone,
            role=payload.role or "citizen",
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    token = create_token(user)
    return LoginResponse(token=token, user=user)


@router.get("/auth/me")
def me(request: Request) -> dict[str, str]:
    auth_header = request.headers.get("authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")

    token = auth_header.split(" ", 1)[1]
    try:
        payload = verify_token(token)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc

    return {
        "email": payload.get("sub", ""),
        "name": payload.get("name", ""),
        "role": payload.get("role", "citizen"),
    }
