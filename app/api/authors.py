# app/api/authors.py
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_
from sqlalchemy.orm import Session
from app.models.books import Author, Book
from app.models.users import User
from app.db import get_db
from app.schemas.authors import (
    AuthorCreate,
    AuthorUpdateFull,
    AuthorUpdatePartial,
    AuthorRead,
)
from app.schemas.books import BookRead
from app.core.security import get_current_user, get_current_admin

router = APIRouter(
    prefix="/api/v1/authors",
    tags=["authors"],
)

# ---------------------------
# 1) 작가 생성 (ADMIN 전용)
# ---------------------------
@router.post(
    "",
    response_model=AuthorRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create Author (ADMIN)",
)
def create_author(
    payload: AuthorCreate,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin),
):
    # 이름 중복 체크
    existing = db.query(Author).filter(Author.name == payload.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Author already exists",
        )

    author = Author(**payload.model_dump())
    db.add(author)
    db.commit()
    db.refresh(author)
    return author


# -----------------------------------------------
# 2) 작가 목록 조회 (검색 + 페이지네이션, USER 이상)
# -----------------------------------------------
@router.get(
    "",
    response_model=List[AuthorRead],
    summary="List Authors",
)
def list_authors(
    keyword: Optional[str] = Query(
        default=None,
        description="이름 / 프로필 검색 (부분 일치)",
    ),
    page: int = Query(0, ge=0, description="페이지 번호 (0부터 시작)"),
    size: int = Query(20, ge=1, le=100, description="페이지 크기"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    query = db.query(Author)

    if keyword:
        like = f"%{keyword}%"
        query = query.filter(
            or_(
                Author.name.like(like),
                Author.profile.like(like),
            )
        )

    authors = (
        query.order_by(Author.author_id.desc())
        .offset(page * size)
        .limit(size)
        .all()
    )

    return authors


# ---------------------------
# 3) 작가 단건 조회 (USER 이상)
# ---------------------------
@router.get(
    "/{author_id}",
    response_model=AuthorRead,
    summary="Get Author",
)
def get_author(
    author_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    author = db.query(Author).filter(Author.author_id == author_id).first()
    if not author:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Author not found",
        )
    return author


# ---------------------------
# 4) 작가 전체 수정 (PUT, ADMIN)
# ---------------------------
@router.put(
    "/{author_id}",
    response_model=AuthorRead,
    summary="Update Author Full (PUT, ADMIN)",
)
def update_author_full(
    author_id: int,
    payload: AuthorUpdateFull,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin),
):
    author = db.query(Author).filter(Author.author_id == author_id).first()
    if not author:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Author not found",
        )

    # PUT: 모든 필드를 덮어씀
    author.name = payload.name
    author.profile = payload.profile

    db.commit()
    db.refresh(author)
    return author


# ---------------------------
# 5) 작가 부분 수정 (PATCH, ADMIN)
# ---------------------------
@router.patch(
    "/{author_id}",
    response_model=AuthorRead,
    summary="Update Author Partial (PATCH, ADMIN)",
)
def update_author_partial(
    author_id: int,
    payload: AuthorUpdatePartial,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin),
):
    author = db.query(Author).filter(Author.author_id == author_id).first()
    if not author:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Author not found",
        )

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(author, field, value)

    db.commit()
    db.refresh(author)
    return author


# ---------------------------
# 6) 작가 삭제 (ADMIN, 하드 삭제)
# ---------------------------
@router.delete("/{author_id}", status_code=status.HTTP_204_NO_CONTENT,
               summary="Delete Author (ADMIN)")
def delete_author(
    author_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    # 1) 작가 존재 여부 확인
    author = db.query(Author).filter(Author.author_id == author_id).first()
    if not author:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Author not found",
        )

    # 2) 이 작가가 쓴 책이 있는지 확인
    has_books = db.query(Book).filter(Book.author_id == author_id).first()
    if has_books:
        # FK 제약 때문에 삭제 불가 → 409 충돌
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot delete author with existing books. Delete or reassign books first.",
        )

    # 3) 실제 삭제
    db.delete(author)
    db.commit()
    return

@router.get("/{author_id}/books",
            response_model=List[BookRead],
            summary="특정 작가의 도서 목록 조회")
def list_author_books(
    author_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    page: int = Query(0, ge=0, description="페이지 번호 (0부터 시작)"),
    size: int = Query(20, ge=1, le=100, description="페이지 크기"),
):
    # 작가 존재 여부 확인
    author = db.query(Author).filter(Author.author_id == author_id).first()
    if not author:
        raise HTTPException(status_code=404, detail="Author not found")

    query = (
        db.query(Book)
        .filter(Book.author_id == author_id)
        .order_by(Book.book_id.desc())
    )

    books = query.offset(page * size).limit(size).all()
    return books