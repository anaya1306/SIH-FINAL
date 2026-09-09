import base64
import hashlib
import hmac
import json
import time
from typing import Any

from app.config import settings


DEFAULT_USERS: dict[str, dict[str, Any]] = {
    "citizen@example.com": {
        "email": "citizen@example.com",
        "password": "password123",
        "name": "Demo Citizen",
        "role": "citizen",
        "phone": "+91 98765 43210",
    },
    "inspector@example.com": {
        "email": "inspector@example.com",
        "password": "password123",
        "name": "Demo Inspector",
        "role": "inspector",
        "phone": "+91 91234 56789",
    },
    "admin@example.com": {
        "email": "admin@example.com",
        "password": "admin123",
        "name": "Demo Admin",
        "role": "admin",
        "phone": "+91 99887 66554",
    },
}

REGISTERED_USERS: dict[str, dict[str, Any]] = {}


def _base64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("utf-8")


def _base64url_decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


def _json_bytes(value: Any) -> bytes:
    return json.dumps(value, separators=(",", ":")).encode("utf-8")


def authenticate_user(email: str, password: str) -> dict[str, Any] | None:
    normalized_email = (email or "").strip().lower()
    if not normalized_email or not password:
        return None

    for user_store in (DEFAULT_USERS, REGISTERED_USERS):
        user = user_store.get(normalized_email)
        if user and user.get("password") == password:
            return {
                "email": user["email"],
                "name": user["name"],
                "role": user["role"],
                "phone": user.get("phone", ""),
            }

    return None


def register_user(name: str, email: str, password: str, phone: str | None = None, role: str = "citizen") -> dict[str, Any]:
    normalized_email = (email or "").strip().lower()
    normalized_name = (name or "").strip()

    if not normalized_name or not normalized_email or not password:
        raise ValueError("Name, email, and password are required")

    if "@" not in normalized_email:
        raise ValueError("Please enter a valid email address")

    if normalized_email in DEFAULT_USERS or normalized_email in REGISTERED_USERS:
        raise ValueError("Account already exists")

    user = {
        "email": normalized_email,
        "password": password,
        "name": normalized_name,
        "role": role,
        "phone": phone or "",
    }

    REGISTERED_USERS[normalized_email] = user
    return {
        "email": user["email"],
        "name": user["name"],
        "role": user["role"],
        "phone": user.get("phone", ""),
    }


def create_token(user: dict[str, Any]) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    now = int(time.time())
    payload = {
        "sub": user.get("email", "demo@packscan.ai"),
        "name": user.get("name", "PackScan User"),
        "role": user.get("role", "citizen"),
        "iat": now,
        "exp": now + 86400,
    }

    encoded_header = _base64url_encode(_json_bytes(header))
    encoded_payload = _base64url_encode(_json_bytes(payload))
    signing_input = f"{encoded_header}.{encoded_payload}".encode("utf-8")
    signature = hmac.new(settings.jwt_secret.encode("utf-8"), signing_input, hashlib.sha256).digest()
    return f"{encoded_header}.{encoded_payload}.{_base64url_encode(signature)}"


def verify_token(token: str) -> dict[str, Any]:
    try:
        header_b64, payload_b64, signature_b64 = token.split(".")
    except ValueError as exc:
        raise ValueError("Invalid token format") from exc

    signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")
    expected_signature = _base64url_encode(
        hmac.new(settings.jwt_secret.encode("utf-8"), signing_input, hashlib.sha256).digest()
    )

    if not hmac.compare_digest(signature_b64, expected_signature):
        raise ValueError("Invalid token signature")

    payload = json.loads(_base64url_decode(payload_b64).decode("utf-8"))
    if payload.get("exp", 0) < int(time.time()):
        raise ValueError("Token expired")

    return payload
