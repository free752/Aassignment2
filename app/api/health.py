from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

import os

from app.db import get_db

router = APIRouter(prefix="/health", tags=["system"])

@router.get("")
def health(db: Session = Depends(get_db)):
    info = {
        "isSuccess": True,
        "message": "OK",
        "version": os.getenv("APP_VERSION", "dev"),
        "buildTime": os.getenv("BUILD_TIME", "unknown"),
        "db": "OK",
    }

    try:
        db.execute(text("SELECT 1"))
        return info
    except SQLAlchemyError:
        # DB 연결/쿼리 실패는 503이 맞음
        raise HTTPException(status_code=503, detail="DB_UNAVAILABLE")
