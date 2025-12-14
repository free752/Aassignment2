# app/models/books.py
from sqlalchemy import Column, BigInteger, String, Text, Date, DateTime,UniqueConstraint,Index, ForeignKey,Integer
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db import Base


class Book(Base):
    __tablename__ = "book"

    book_id = Column(BigInteger, primary_key=True, autoincrement=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    isbn = Column(String(20), unique=True, nullable=True)
    price = Column(Integer, nullable=False)
    stock = Column(Integer, nullable=False, default=0)

    status = Column(String(20), nullable=False, default="active")  # normal / hidden 등
    published_date = Column(Date, nullable=True)

    favorites = relationship("Favorite", back_populates="book")
    author_id = Column(BigInteger, ForeignKey("authors.author_id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # 나중에 Author 모델 만들면 여기에 관계 연결
    author = relationship("Author", back_populates="books", lazy="joined")

class Author(Base):
    __tablename__ = "authors"

    author_id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    profile = Column(Text, nullable=True)

    # Book 쪽과 양방향 관계
    books = relationship("Book", back_populates="author")

class Favorite(Base):
    __tablename__ = "favorite"

    favorite_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("user.user_id"), nullable=False)
    book_id = Column(BigInteger, ForeignKey("book.book_id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="favorites")
    book = relationship("Book", back_populates="favorites")

    __table_args__ = (
        # DB 명세: UNIQUE(user_id, book_id), (user_id, created_at)
        UniqueConstraint("user_id", "book_id", name="uq_favorite_user_book"),
        Index("ix_favorite_user_created_at", "user_id", "created_at"),
    )