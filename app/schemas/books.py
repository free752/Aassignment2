# app/schemas/books.py
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel


class BookBase(BaseModel):
    title: str
    description: Optional[str] = None
    isbn: Optional[str] = None
    price: int
    stock: int = 0
    status: str = "active"
    published_date: Optional[date] = None
    author_id: int


class BookCreate(BookBase):
    """도서 등록에 사용할 스키마"""
    pass


class BookUpdateFull(BookBase):
    """PUT: 전체 수정용 (필수 필드는 전부 있어야 함)"""
    pass

class BookUpdatePartial(BaseModel):
    """PATCH: 부분 수정용 (전부 선택)"""
    title: Optional[str] = None
    description: Optional[str] = None
    isbn: Optional[str] = None
    price: Optional[int] = None
    stock: Optional[int] = None
    status: Optional[str] = None
    published_date: Optional[date] = None
    author_id: Optional[int] = None

class BookRead(BookBase):
    """조회용 스키마"""
    book_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class BookPut(BaseModel):
    title: Optional[str] = None
    price: Optional[int] = None
    stock: Optional[int] = None
    author_id: Optional[int] = None