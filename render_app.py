"""Render entry point with optional family-only HTTP Basic authentication."""

from __future__ import annotations

import base64
import hmac
import os
from pathlib import Path

from fastapi import Request
from fastapi.responses import JSONResponse, Response

from app import app


PUBLIC_PATHS = {"/health"}


def _credentials() -> tuple[str, str]:
    return (
        os.getenv("FAMILY_USERNAME", "").strip(),
        os.getenv("FAMILY_PASSWORD", "").strip(),
    )


def _authorized(request: Request, expected_user: str, expected_password: str) -> bool:
    header = request.headers.get("authorization", "")
    if not header.startswith("Basic "):
        return False

    try:
        decoded = base64.b64decode(header[6:], validate=True).decode("utf-8")
        supplied_user, supplied_password = decoded.split(":", 1)
    except (ValueError, UnicodeDecodeError):
        return False

    return hmac.compare_digest(supplied_user, expected_user) and hmac.compare_digest(
        supplied_password, expected_password
    )


@app.middleware("http")
async def family_authentication(request: Request, call_next):
    if request.url.path in PUBLIC_PATHS:
        return await call_next(request)

    expected_user, expected_password = _credentials()
    if not expected_user or not expected_password:
        return JSONResponse(
            status_code=503,
            content={
                "detail": "Set FAMILY_USERNAME and FAMILY_PASSWORD in Render before using the site."
            },
        )

    if not _authorized(request, expected_user, expected_password):
        return Response(
            status_code=401,
            content="Family login required",
            headers={
                "WWW-Authenticate": 'Basic realm="Family TikTok Downloader", charset="UTF-8"',
                "Cache-Control": "no-store",
            },
            media_type="text/plain",
        )

    return await call_next(request)


@app.get("/health", include_in_schema=False)
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.on_event("startup")
def remove_stale_temporary_files() -> None:
    """Clear generated files whenever a fresh Render instance starts."""
    base_dir = Path(__file__).resolve().parent
    for folder_name in ("outputs", "uploads"):
        folder = base_dir / folder_name
        folder.mkdir(exist_ok=True)
        for item in folder.iterdir():
            if item.is_file():
                try:
                    item.unlink()
                except OSError:
                    pass
