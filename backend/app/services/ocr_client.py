"""Client for packaging-ocr API."""

from __future__ import annotations

import httpx

from app.config import settings


OCR_API_URL = settings.ocr_api_url.rstrip("/")
OCR_API_KEY = settings.ocr_api_key


async def call_ocr_api(
    image_bytes: bytes,
    *,
    mode: str = "citizen",
    engine: str = "auto",
    languages: str | None = None,
) -> dict:
    """Call the packaging-ocr API and return the result dict."""
    headers = {}
    if OCR_API_KEY:
        headers["X-API-Key"] = OCR_API_KEY
    headers["X-OCR-Mode"] = mode

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{OCR_API_URL}/v1/ocr",
            files={"file": ("image.jpg", image_bytes, "image/jpeg")},
            data={"engine": engine, "languages": languages or ""},
            headers=headers,
        )
        response.raise_for_status()
        return response.json()


def call_ocr_api_sync(
    image_bytes: bytes,
    *,
    mode: str = "citizen",
    engine: str = "auto",
    languages: str | None = None,
) -> dict:
    """Synchronous version for use in threads."""
    headers = {}
    if OCR_API_KEY:
        headers["X-API-Key"] = OCR_API_KEY
    headers["X-OCR-Mode"] = mode

    with httpx.Client(timeout=60.0) as client:
        response = client.post(
            f"{OCR_API_URL}/v1/ocr",
            files={"file": ("image.jpg", image_bytes, "image/jpeg")},
            data={"engine": engine, "languages": languages or ""},
            headers=headers,
        )
        response.raise_for_status()
        return response.json()
