# app/core/error_handlers.py
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict

from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException


def _now_iso_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _shape(
    *,
    request: Request,
    status: int,
    code: str,
    message: str,
    details: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    return {
        "timestamp": _now_iso_utc(),
        "path": request.url.path,
        "status": status,
        "code": code,
        "message": message,
        "details": details or {},
    }


async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    # 우리가 raise_http()로 던지면 detail이 dict 형태
    if isinstance(exc.detail, dict):
        d = exc.detail
        return JSONResponse(
            status_code=exc.status_code,
            content=_shape(
                request=request,
                status=exc.status_code,
                code=str(d.get("code", f"HTTP_{exc.status_code}")),
                message=str(d.get("message", "")),
                details=d.get("details", {}) or {},
            ),
        )

    # 기존처럼 detail이 문자열이어도 규격 맞춰서 내려줌
    return JSONResponse(
        status_code=exc.status_code,
        content=_shape(
            request=request,
            status=exc.status_code,
            code=f"HTTP_{exc.status_code}",
            message=str(exc.detail),
            details={},
        ),
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content=_shape(
            request=request,
            status=422,
            code="VALIDATION_ERROR",
            message="validation error",
            details={"errors": exc.errors()},
        ),
    )


async def unhandled_exception_handler(request: Request, exc: Exception):
    # 스택트레이스는 서버 로그에 찍히고, 응답은 민감정보 없이 통일
    return JSONResponse(
        status_code=500,
        content=_shape(
            request=request,
            status=500,
            code="INTERNAL_ERROR",
            message="internal server error",
            details={},
        ),
    )
