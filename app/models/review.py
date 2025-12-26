# app/models/review.py
from __future__ import annotations

from sqlalchemy import (
    BigInteger, SmallInteger, Integer, Text, DateTime,
    ForeignKey, UniqueConstraint, func
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.db import Base


class Review(Base):
    __tablename__ = "review"

    review_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("user.user_id"), nullable=False, index=True)
    book_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("book.book_id"), nullable=False, index=True)

    content: Mapped[str] = mapped_column(Text, nullable=False)
    rating: Mapped[int] = mapped_column(SmallInteger, nullable=False)  # validation은 Pydantic에서 1~5로
    like_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    created_at: Mapped["DateTime"] = mapped_column(DateTime, nullable=False, server_default=func.now())
    updated_at: Mapped["DateTime"] = mapped_column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    deleted_at: Mapped["DateTime | None"] = mapped_column(DateTime, nullable=True)

    # 관계
    user = relationship("User", lazy="joined")      # 네 User 모델 클래스명에 맞춰
    book = relationship("Book", lazy="joined")      # 네 Book 모델 클래스명에 맞춰
    likes = relationship("ReviewLike", back_populates="review", cascade="all, delete-orphan")
    comments = relationship("Comment", back_populates="review", cascade="all, delete-orphan")


class ReviewLike(Base):
    __tablename__ = "review_like"
    __table_args__ = (
        UniqueConstraint("user_id", "review_id", name="uq_review_like_user_review"),
    )

    review_like_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("user.user_id"), nullable=False, index=True)
    review_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("review.review_id"), nullable=False, index=True)

    created_at: Mapped["DateTime"] = mapped_column(DateTime, nullable=False, server_default=func.now())

    user = relationship("User", lazy="joined")
    review = relationship("Review", back_populates="likes")


class Comment(Base):
    __tablename__ = "comment"

    comment_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("user.user_id"), nullable=False, index=True)
    review_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("review.review_id"), nullable=False, index=True)

    # ERD 컬럼명이 comment(text)라서 그대로 둠(API에서는 content로 노출 추천)
    comment: Mapped[str] = mapped_column(Text, nullable=False)
    like_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    created_at: Mapped["DateTime"] = mapped_column(DateTime, nullable=False, server_default=func.now())
    updated_at: Mapped["DateTime"] = mapped_column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    deleted_at: Mapped["DateTime | None"] = mapped_column(DateTime, nullable=True)

    user = relationship("User", lazy="joined")
    review = relationship("Review", back_populates="comments")
    likes = relationship("CommentLike", back_populates="comment_obj", cascade="all, delete-orphan")


class CommentLike(Base):
    __tablename__ = "comment_like"
    __table_args__ = (
        UniqueConstraint("user_id", "comment_id", name="uq_comment_like_user_comment"),
    )

    comment_like_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("user.user_id"), nullable=False, index=True)
    comment_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("comment.comment_id"), nullable=False, index=True)

    created_at: Mapped["DateTime"] = mapped_column(DateTime, nullable=False, server_default=func.now())

    user = relationship("User", lazy="joined")
    # Comment.comment 이랑 이름 충돌 피하려고 comment_obj
    comment_obj = relationship("Comment", back_populates="likes")
