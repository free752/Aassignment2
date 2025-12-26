# app/schemas/review.py
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List


class ReviewCreate(BaseModel):
    content: str = Field(min_length=1)
    rating: int = Field(ge=1, le=5)


class ReviewUpdate(BaseModel):
    content: Optional[str] = Field(default=None, min_length=1)
    rating: Optional[int] = Field(default=None, ge=1, le=5)


class ReviewOut(BaseModel):
    review_id: int
    user_id: int
    book_id: int
    content: str
    rating: int
    like_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CommentCreate(BaseModel):
    content: str = Field(min_length=1)


class CommentUpdate(BaseModel):
    content: Optional[str] = Field(default=None, min_length=1)


class CommentOut(BaseModel):
    comment_id: int
    user_id: int
    review_id: int
    comment: str
    like_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PageMeta(BaseModel):
    page: int
    size: int
    total: int


class ReviewListResponse(BaseModel):
    content: List[ReviewOut]
    meta: PageMeta


class CommentListResponse(BaseModel):
    content: List[CommentOut]
    meta: PageMeta
