# app/api/favorites.py
import math
from datetime import datetime, timezone
from typing import List
from sqlalchemy import func
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.schemas.common import FavoriteListPage
from app.db import get_db
from app.models.books import Favorite, Book
from app.models.users import User
from app.core.security import get_current_user
from app.schemas.favorites import FavoriteCreate, FavoriteRead


router = APIRouter(
    prefix="/api/v1/favorites",
    tags=["favorites"],
)

# 600. 위시리스트 추가
# app/api/favorites.py

@router.post("", response_model=FavoriteRead, status_code=status.HTTP_201_CREATED)
def add_favorite(
    payload: FavoriteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # 1) 책 존재 확인
    book = (
        db.query(Book)
        .filter(Book.book_id == payload.book_id)
        .first()
    )
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="BOOK_NOT_FOUND",
        )

    # 2) 이미 즐겨찾기 되어 있는지 확인
    favorite = (
        db.query(Favorite)
        .filter(
            Favorite.user_id == current_user.user_id,
            Favorite.book_id == payload.book_id,
        )
        .first()
    )
    if favorite:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="FAVORITE_ALREADY_EXISTS",
        )

    # 3) 새 즐겨찾기 생성
    favorite = Favorite(
        user_id=current_user.user_id,
        book_id=payload.book_id,
        created_at=datetime.utcnow(),
    )
    db.add(favorite)
    db.commit()
    db.refresh(favorite)

    return FavoriteRead(
        favorite_id=favorite.favorite_id,
        book_id=book.book_id,
        title=book.title,
    )


# 601. 내 위시리스트 조회
@router.get("", response_model=FavoriteListPage)
def list_favorites(
    page: int = 0,
    size: int = 20,
    sort: str = Query("created_at,desc"),  # 추가
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    base_q = (
        db.query(Favorite, Book)
        .join(Book, Favorite.book_id == Book.book_id)
        .filter(
            Favorite.user_id == current_user.user_id,
            Favorite.deleted_at.is_(None),
        )
    )

    field, direction = (sort.split(",") + ["desc"])[:2]
    direction = direction.lower()
    sort_map = {
        "favorite_id": Favorite.favorite_id,
        "created_at": Favorite.created_at,
    }
    col = sort_map.get(field, Favorite.created_at)


    total = base_q.with_entities(func.count(func.distinct(Favorite.favorite_id))).scalar()
    ordered_q = base_q.order_by(col.asc() if direction == "asc" else col.desc())
    rows = ordered_q.offset(page * size).limit(size).all()
    total_pages = (total + size - 1) // size
    content = [
        {"favorite_id": fav.favorite_id, "book_id": book.book_id, "title": book.title}
        for fav, book in rows
    ]

    return {
    "content": content,
    "page": page,
    "size": size,
    "totalElements": total,
    "totalPages": total_pages,
    "sort": sort,
    }


# 602. 즐겨찾기 삭제 (멱등)
@router.delete("/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_favorite(
    book_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    favorite = db.query(Favorite).filter(
        Favorite.user_id == current_user.user_id,
        Favorite.book_id == book_id,
    ).first()

    if not favorite:
        raise HTTPException(status_code=404, detail="FAVORITE_NOT_FOUND")

    db.delete(favorite)
    db.commit()
    return