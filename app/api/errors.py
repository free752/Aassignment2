# app/api/errors.py (기존 errors.py 대체)
from fastapi import APIRouter
from app.core.error_codes import ErrorCode, raise_http

router = APIRouter(prefix="/errors", tags=["errors"])


@router.get("/400")
def e400():
    raise_http(ErrorCode.INVALID_REQUEST)

@router.get("/401")
def e401():
    raise_http(ErrorCode.AUTH_REQUIRED)

@router.get("/403")
def e403():
    raise_http(ErrorCode.FORBIDDEN)

@router.get("/404")
def e404():
    raise_http(ErrorCode.NOT_FOUND)

@router.get("/409")
def e409():
    raise_http(ErrorCode.CONFLICT)

@router.get("/422")
def e422():
    raise_http(ErrorCode.VALIDATION_ERROR, status_code=422)

@router.get("/429")
def e429():
    raise_http(ErrorCode.RATE_LIMITED)

@router.get("/500")
def e500():
    # 의도적으로 “Unhandled” 만들어서 500 핸들러 타게
    raise RuntimeError("forced 500")

@router.get("/503")
def e503():
    raise_http(ErrorCode.DB_UNAVAILABLE)
