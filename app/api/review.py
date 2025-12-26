# app/api/reviews.py
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from app.db import get_db  # 프로젝트에 맞게 수정
from app.core.security import get_current_user  # 프로젝트에 맞게 수정
from app.models.review import Review, ReviewLike, Comment, CommentLike
from app.models.books import Book  # 프로젝트 Book 모델 import 경로 맞추기
from app.schemas.review import (
    ReviewCreate, ReviewUpdate, ReviewOut, ReviewListResponse, PageMeta,
    CommentCreate, CommentUpdate, CommentOut, CommentListResponse
)

router = APIRouter(prefix="/api/v1", tags=["Reviews"])


def _ensure_book(db: Session, book_id: int) -> Book:
    book = db.get(Book, book_id)
    if not book or getattr(book, "deleted_at", None) is not None:
        raise HTTPException(status_code=404, detail="BOOK_NOT_FOUND")
    return book


def _ensure_review(db: Session, review_id: int) -> Review:
    review = db.get(Review, review_id)
    if not review or review.deleted_at is not None:
        raise HTTPException(status_code=404, detail="REVIEW_NOT_FOUND")
    return review


def _ensure_comment(db: Session, comment_id: int) -> Comment:
    c = db.get(Comment, comment_id)
    if not c or c.deleted_at is not None:
        raise HTTPException(status_code=404, detail="COMMENT_NOT_FOUND")
    return c


# ---------- Reviews ----------
@router.post("/books/{book_id}/reviews", response_model=ReviewOut, status_code=status.HTTP_201_CREATED)
def create_review(
    book_id: int,
    body: ReviewCreate,
    db: Session = Depends(get_db),
    me=Depends(get_current_user),
):
    _ensure_book(db, book_id)

    review = Review(
        user_id=me.user_id,
        book_id=book_id,
        content=body.content,
        rating=body.rating,
        like_count=0,
    )
    db.add(review)
    db.commit()
    db.refresh(review)
    return review


@router.get("/books/{book_id}/reviews", response_model=ReviewListResponse)
def list_book_reviews(
    book_id: int,
    page: int = Query(0, ge=0),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    _ensure_book(db, book_id)

    total = db.scalar(
        select(func.count()).select_from(Review).where(
            Review.book_id == book_id,
            Review.deleted_at.is_(None),
        )
    )

    rows = db.scalars(
        select(Review).where(
            Review.book_id == book_id,
            Review.deleted_at.is_(None),
        ).order_by(Review.created_at.desc())
        .offset(page * size).limit(size)
    ).all()

    return ReviewListResponse(content=rows, meta=PageMeta(page=page, size=size, total=total or 0))


@router.get("/reviews/{review_id}", response_model=ReviewOut)
def get_review(review_id: int, db: Session = Depends(get_db)):
    return _ensure_review(db, review_id)


@router.patch("/reviews/{review_id}", response_model=ReviewOut)
def update_review(
    review_id: int,
    body: ReviewUpdate,
    db: Session = Depends(get_db),
    me=Depends(get_current_user),
):
    review = _ensure_review(db, review_id)
    if review.user_id != me.user_id and getattr(me, "role", None) != "admin":
        raise HTTPException(status_code=403, detail="FORBIDDEN")

    if body.content is not None:
        review.content = body.content
    if body.rating is not None:
        review.rating = body.rating

    db.commit()
    db.refresh(review)
    return review


@router.delete("/reviews/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_review(
    review_id: int,
    db: Session = Depends(get_db),
    me=Depends(get_current_user),
):
    review = _ensure_review(db, review_id)
    if review.user_id != me.user_id and getattr(me, "role", None) != "admin":
        raise HTTPException(status_code=403, detail="FORBIDDEN")

    # soft delete
    review.deleted_at = func.now()
    db.commit()
    return None


# ---------- Review Like ----------
@router.post("/reviews/{review_id}/like", status_code=status.HTTP_201_CREATED)
def like_review(
    review_id: int,
    db: Session = Depends(get_db),
    me=Depends(get_current_user),
):
    review = _ensure_review(db, review_id)

    like = ReviewLike(user_id=me.user_id, review_id=review.review_id)
    db.add(like)

    try:
        # 중복 좋아요는 DB unique constraint로 방어
        review.like_count += 1
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="DUPLICATE_REVIEW_LIKE")

    return {"review_id": review.review_id, "like_count": review.like_count}


@router.delete("/reviews/{review_id}/like", status_code=status.HTTP_200_OK)
def unlike_review(
    review_id: int,
    db: Session = Depends(get_db),
    me=Depends(get_current_user),
):
    review = _ensure_review(db, review_id)

    row = db.scalar(
        select(ReviewLike).where(
            ReviewLike.review_id == review.review_id,
            ReviewLike.user_id == me.user_id
        )
    )
    if not row:
        raise HTTPException(status_code=404, detail="REVIEW_LIKE_NOT_FOUND")

    db.delete(row)
    review.like_count = max(0, review.like_count - 1)
    db.commit()

    return {"review_id": review.review_id, "like_count": review.like_count}


# ---------- Comments ----------
@router.post("/reviews/{review_id}/comments", response_model=CommentOut, status_code=status.HTTP_201_CREATED)
def create_comment(
    review_id: int,
    body: CommentCreate,
    db: Session = Depends(get_db),
    me=Depends(get_current_user),
):
    review = _ensure_review(db, review_id)

    c = Comment(
        user_id=me.user_id,
        review_id=review.review_id,
        comment=body.content,   # API는 content, DB 컬럼은 comment
        like_count=0,
    )
    db.add(c)
    db.commit()
    db.refresh(c)
    return c


@router.get("/reviews/{review_id}/comments", response_model=CommentListResponse)
def list_comments(
    review_id: int,
    page: int = Query(0, ge=0),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    review = _ensure_review(db, review_id)

    total = db.scalar(
        select(func.count()).select_from(Comment).where(
            Comment.review_id == review.review_id,
            Comment.deleted_at.is_(None),
        )
    )

    rows = db.scalars(
        select(Comment).where(
            Comment.review_id == review.review_id,
            Comment.deleted_at.is_(None),
        ).order_by(Comment.created_at.asc())
        .offset(page * size).limit(size)
    ).all()

    return CommentListResponse(content=rows, meta=PageMeta(page=page, size=size, total=total or 0))


@router.patch("/comments/{comment_id}", response_model=CommentOut)
def update_comment(
    comment_id: int,
    body: CommentUpdate,
    db: Session = Depends(get_db),
    me=Depends(get_current_user),
):
    c = _ensure_comment(db, comment_id)
    if c.user_id != me.user_id and getattr(me, "role", None) != "admin":
        raise HTTPException(status_code=403, detail="FORBIDDEN")

    if body.content is not None:
        c.comment = body.content

    db.commit()
    db.refresh(c)
    return c


@router.delete("/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_comment(
    comment_id: int,
    db: Session = Depends(get_db),
    me=Depends(get_current_user),
):
    c = _ensure_comment(db, comment_id)
    if c.user_id != me.user_id and getattr(me, "role", None) != "admin":
        raise HTTPException(status_code=403, detail="FORBIDDEN")

    c.deleted_at = func.now()
    db.commit()
    return None


# ---------- Comment Like ----------
@router.post("/comments/{comment_id}/like", status_code=status.HTTP_201_CREATED)
def like_comment(
    comment_id: int,
    db: Session = Depends(get_db),
    me=Depends(get_current_user),
):
    c = _ensure_comment(db, comment_id)

    like = CommentLike(user_id=me.user_id, comment_id=c.comment_id)
    db.add(like)

    try:
        c.like_count += 1
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="DUPLICATE_COMMENT_LIKE")

    return {"comment_id": c.comment_id, "like_count": c.like_count}


@router.delete("/comments/{comment_id}/like", status_code=status.HTTP_200_OK)
def unlike_comment(
    comment_id: int,
    db: Session = Depends(get_db),
    me=Depends(get_current_user),
):
    c = _ensure_comment(db, comment_id)

    row = db.scalar(
        select(CommentLike).where(
            CommentLike.comment_id == c.comment_id,
            CommentLike.user_id == me.user_id
        )
    )
    if not row:
        raise HTTPException(status_code=404, detail="COMMENT_LIKE_NOT_FOUND")

    db.delete(row)
    c.like_count = max(0, c.like_count - 1)
    db.commit()

    return {"comment_id": c.comment_id, "like_count": c.like_count}
