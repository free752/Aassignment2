# app/api/books.py
from typing import List, Optional
from app.models.users import User
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.db import get_db
from app.core.security import require_admin
from app.schemas.authors import AuthorRead
from app.schemas.books import BookCreate, BookUpdateFull, BookUpdatePartial, BookRead, BookPut
from app.core.security import get_current_user, get_current_admin  # 이미 있는 함수 재사용
from app.models.books import Book, Author

from sqlalchemy.exc import IntegrityError

router = APIRouter(prefix="/api/v1/books", tags=["books"])

@router.put("/{book_id}")
def put_book(book_id: int, body: BookPut, db: Session = Depends(get_db), _admin=Depends(require_admin)):
    book = db.query(Book).filter(Book.book_id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="BOOK_NOT_FOUND")

    data = body.model_dump(exclude_none=True)

    # ✅ author_id가 들어왔으면 미리 존재 여부 검사
    if "author_id" in data:
        author = db.query(Author).filter(Author.author_id == data["author_id"]).first()
        if not author:
            raise HTTPException(status_code=400, detail="INVALID_AUTHOR_ID")

    for k, v in data.items():
        setattr(book, k, v)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        # 혹시 다른 FK/UNIQUE 터져도 400으로 정리
        raise HTTPException(status_code=400, detail="INVALID_REQUEST")
    db.refresh(book)

    return {"isSuccess": True, "message": "OK", "payload": {"book_id": book.book_id}}

@router.get("", response_model=list[BookRead], summary="전체 도서 목록 조회 (부분 검색)")
def list_books(
        keyword: Optional[str] = Query(None, description="제목 / 설명 검색 (부분 일치)"),
        db: Session = Depends(get_db),
        current_user=Depends(get_current_user), # 관리자 전용이면 유지
):
    query = db.query(Book)

    if keyword:
        like = f"%{keyword}%"
        query = query.filter(
            or_(Book.title.like(like), Book.description.like(like))
        )

    books = query.order_by(Book.book_id.desc()).all()

    # ✅ 반드시 리스트를 리턴해야 함
    return books

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
    current_admin: User = Depends(get_current_admin),
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