# app/core/error_codes.py
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional, Dict

from fastapi import HTTPException


class ErrorCode(str, Enum):
    # 400
    INVALID_REQUEST = "INVALID_REQUEST"
    INVALID_AUTHOR_ID = "INVALID_AUTHOR_ID"

    # 401
    AUTH_REQUIRED = "AUTH_REQUIRED"
    TOKEN_INVALID = "TOKEN_INVALID"

    # 403
    FORBIDDEN = "FORBIDDEN"

    # 404
    NOT_FOUND = "NOT_FOUND"
    BOOK_NOT_FOUND = "BOOK_NOT_FOUND"
    AUTHOR_NOT_FOUND = "AUTHOR_NOT_FOUND"
    ORDER_NOT_FOUND = "ORDER_NOT_FOUND"

    # 409
    CONFLICT = "CONFLICT"
    ALREADY_CANCELED = "ALREADY_CANCELED"

    # 422
    VALIDATION_ERROR = "VALIDATION_ERROR"

    # 429
    RATE_LIMITED = "RATE_LIMITED"

    # 500+
    INTERNAL_ERROR = "INTERNAL_ERROR"
    DB_UNAVAILABLE = "DB_UNAVAILABLE"


@dataclass(frozen=True)
class ErrorSpec:
    status: int
    message: str


ERROR_SPECS: Dict[ErrorCode, ErrorSpec] = {
    ErrorCode.INVALID_REQUEST: ErrorSpec(400, "invalid request"),
    ErrorCode.INVALID_AUTHOR_ID: ErrorSpec(400, "author_id does not exist"),

    ErrorCode.AUTH_REQUIRED: ErrorSpec(401, "authentication required"),
    ErrorCode.TOKEN_INVALID: ErrorSpec(401, "invalid or expired token"),

    ErrorCode.FORBIDDEN: ErrorSpec(403, "forbidden"),

    ErrorCode.NOT_FOUND: ErrorSpec(404, "resource not found"),
    ErrorCode.BOOK_NOT_FOUND: ErrorSpec(404, "book not found"),
    ErrorCode.AUTHOR_NOT_FOUND: ErrorSpec(404, "author not found"),
    ErrorCode.ORDER_NOT_FOUND: ErrorSpec(404, "order not found"),

    ErrorCode.CONFLICT: ErrorSpec(409, "conflict"),
    ErrorCode.ALREADY_CANCELED: ErrorSpec(409, "already canceled"),

    ErrorCode.VALIDATION_ERROR: ErrorSpec(422, "validation error"),

    ErrorCode.RATE_LIMITED: ErrorSpec(429, "too many requests"),

    ErrorCode.INTERNAL_ERROR: ErrorSpec(500, "internal server error"),
    ErrorCode.DB_UNAVAILABLE: ErrorSpec(503, "db unavailable"),
}


def raise_http(
    code: ErrorCode,
    *,
    message: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    status_code: Optional[int] = None,
) -> None:
    spec = ERROR_SPECS.get(code, ERROR_SPECS[ErrorCode.INTERNAL_ERROR])
    raise HTTPException(
        status_code=status_code or spec.status,
        detail={
            "code": code.value,
            "message": message or spec.message,
            "details": details or {},
        },
    )
