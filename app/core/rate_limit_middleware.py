# app/core/rate_limit_middleware.py
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse
import time

# 전역 메모리 저장소: {ip: [timestamp, ...]}
_REQ_LOG = {}

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, max_requests: int = 30, window_seconds: int = 10):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds

    async def dispatch(self, request, call_next):
        path = request.url.path

        # 예외 path
        if path in ("/health", "/docs", "/openapi.json", "/redoc"):
            return await call_next(request)

        # IP 추출 (프록시 없으면 보통 여기로 잡힘)
        xff = request.headers.get("x-forwarded-for")
        ip = (xff.split(",")[0].strip() if xff else (request.client.host if request.client else "unknown"))

        now = time.time()
        window_start = now - self.window_seconds

        times = _REQ_LOG.get(ip, [])
        # 윈도우 밖 기록 제거
        times = [t for t in times if t >= window_start]
        times.append(now)
        _REQ_LOG[ip] = times

        exceeded = len(times) > self.max_requests

        if exceeded:
            return JSONResponse(
                status_code=429,
                content={
                    "code": "RATE_LIMITED",
                    "message": "Too many requests",
                    "details": {
                        "max_requests": self.max_requests,
                        "window_seconds": self.window_seconds,
                    },
                },
            )

        return await call_next(request)
