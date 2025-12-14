# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import favorites
from app.core.config import get_settings
from app.api.users import router as users_router
from app.api.auth import router as auth_router
from app.api.books import router as books_router
from app.api.authors import router as authors_router
from app.core.logging_middleware import LoggingMiddleware
from app.api.cart import router as cart_router
from app.api.orders import router as orders_router
from app.api.errors import router as test_router
from app.api.health import router as health_router
from app.core.rate_limit_middleware import RateLimitMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.core.error_handlers import (
    http_exception_handler,
    validation_exception_handler,
    unhandled_exception_handler,
)



settings = get_settings()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)




# ★ users 라우터 등록
app.include_router(users_router)

app.include_router(auth_router)

app.add_middleware(LoggingMiddleware)
app.include_router(books_router)
app.include_router(authors_router)
app.include_router(favorites.router)
app.include_router(cart_router)
app.include_router(orders_router)
app.include_router(test_router)
app.include_router(health_router)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)
app.add_middleware(RateLimitMiddleware, max_requests=30, window_seconds=10)