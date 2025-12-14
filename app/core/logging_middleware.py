# app/core/logging_middleware.py
import time
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

logger = logging.getLogger("uvicorn.error")

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.time()

        response = await call_next(request)

        process_ms = (time.time() - start) * 1000
        logger.info(
            f"{request.client.host} {request.method} {request.url.path} "
            f"-> {response.status_code} ({process_ms:.2f}ms)"
        )

        return response
