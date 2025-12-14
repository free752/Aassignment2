# app/api/books.py
from typing import List, Optional
import math
from app.models.users import User
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_,asc, desc
from app.db import get_db
from app.core.security import require_admin
from app.schemas.authors import AuthorRead
from app.schemas.books import BookCreate, BookUpdateFull, BookUpdatePartial, BookRead, BookPut
from app.core.security import get_current_user, get_current_admin  # 이미 있는 함수 재사용
from app.models.books import Book, Author
from pydantic import BaseModel

from app.core.error_codes import raise_http, ErrorCode
from sqlalchemy.exc import IntegrityError

class BookPage(BaseModel):
    content: list[BookRead]
    page: int
    size: int
    totalElements: int
    totalPages: int
    sort: str
router = APIRouter(prefix="/api/v1/books", tags=["books"])



@router.get("", summary="전체 도서 목록 조회 (부분 검색)")
def list_books(
    db: Session = Depends(get_db),
    keyword: str | None = Query(None),
    page: int = Query(0, ge=0),
    size: int = Query(20, ge=1, le=100),
    sort: str = Query("created_at,desc"),  # e.g. title,asc / price,desc / created_at,desc
):
    query = db.query(Book)

    if keyword:
        like = f"%{keyword}%"
        query = query.filter((Book.title.ilike(like)) | (Book.description.ilike(like)))

    total = query.count()

    # sort 파싱
    field, direction = (sort.split(",") + ["desc"])[:2]
    direction = direction.lower()

    sort_map = {
        "created_at": Book.created_at,
        "title": Book.title,
        "price": Book.price,
    }
    col = sort_map.get(field, Book.created_at)
    query = query.order_by(col.asc() if direction == "asc" else col.desc())

    items = (
        query.offset(page * size)
             .limit(size)
             .all()
    )

    total_pages = math.ceil(total / size) if size else 0

    return {
        "isSuccess": True,
        "message": "OK",
        "payload": {
            "content": items,
            "page": page,
            "size": size,
            "totalElements": total,
            "totalPages": total_pages,
            "sort": sort,
        },
    }

@router.get("/{book_id}", response_model=BookRead, summary="도서 상세 조회")
def get_book(book_id: int, db: Session = Depends(get_db)):
    book = db.query(Book).filter(Book.book_id == book_id).first()
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found",
        )
    return book





@router.put(
    "/{book_id}",
    response_model=BookRead,
    summary="도서 전체 수정 (ADMIN)",
)
def update_book_full(
    book_id: int,
    payload: BookUpdateFull,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    book = db.query(Book).filter(Book.book_id == book_id).first()
    if not book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")

    # author_id 유효성 검사
    author = db.query(Author).filter(Author.author_id == payload.author_id).first()
    if not author:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid author_id")

    # === 전체 필드 덮어쓰기 (조건문 없음) ===
    book.title = payload.title
    book.description = payload.description
    book.isbn = payload.isbn
    book.price = payload.price
    book.stock = payload.stock
    book.status = payload.status
    book.published_date = payload.published_date
    book.author_id = payload.author_id

    db.commit()
    db.refresh(book)
    return book

@router.patch(
    "/{book_id}",
    response_model=BookRead,
    summary="도서 부분 수정 (ADMIN)",
)
def update_book_partial(
    book_id: int,
    payload: BookUpdatePartial,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    book = db.query(Book).filter(Book.book_id == book_id).first()
    if not book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")

    if payload.title is not None:
        book.title = payload.title
    if payload.description is not None:
        book.description = payload.description
    if payload.isbn is not None:
        book.isbn = payload.isbn
    if payload.price is not None:
        book.price = payload.price
    if payload.stock is not None:
        book.stock = payload.stock
    if payload.status is not None:
        book.status = payload.status
    if payload.published_date is not None:
        book.published_date = payload.published_date
    if payload.author_id is not None:
        author = db.query(Author).filter(Author.author_id == payload.author_id).first()
        if not author:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid author_id")
        book.author_id = payload.author_id

    db.commit()
    db.refresh(book)
    return book

@router.delete("/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_book(
    book_id: int,
    db: Session = Depends(get_db),
    admin = Depends(get_current_admin),
):
    book = db.query(Book).filter(Book.book_id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    db.delete(book)
    db.commit()
    return None

@router.get("/{book_id}/author",
            response_model=AuthorRead,
            summary="도서의 작가 정보 조회")
def get_book_author(
    book_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    book = db.query(Book).filter(Book.book_id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    if not book.author:
        # 이론상 FK 때문에 거의 없겠지만, 방어 코드
        raise HTTPException(status_code=404, detail="Author not found")

    return book.author

@router.post(
    "",
    response_model=BookRead,
    status_code=status.HTTP_201_CREATED,
    summary="도서 생성 (ADMIN)",
)
def create_book(
    payload: BookCreate,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),  # ADMIN만
):
    # author_id 유효성 검사
    author = db.query(Author).filter(Author.author_id == payload.author_id).first()
    if not author:
        raise_http(
            ErrorCode.INVALID_AUTHOR_ID,
            details={"author_id": payload.author_id},
            status_code=400,
        )

    book = Book(**payload.model_dump())

    db.add(book)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise_http(ErrorCode.CONFLICT, message="duplicate constraint", status_code=409)

    db.refresh(book)
    return book