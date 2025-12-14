from datetime import datetime
from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    String,
    Text,
    Index,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import relationship

from app.db import Base


gender_enum = Enum("male", "female", name="gender_list")
user_role_enum = Enum("user", "admin", name="user_role")


class User(Base):
    __tablename__ = "user"

    user_id = Column(BigInteger, primary_key=True, autoincrement=True)

    email = Column(String(255), nullable=False, unique=True)
    password = Column(String(255), nullable=False)

    name = Column(String(255), nullable=False)
    is_korean = Column(Boolean, nullable=False, default=True)

    address = Column(String(255), nullable=True)
    phone_number = Column(String(50), nullable=True)

    birth_date = Column(Date, nullable=True)
    gender = Column(gender_enum, nullable=True)

    profile = Column(Text, nullable=True)
    from app.models.books import Favorite
    email_verified_at = Column(DateTime, nullable=True)
    status = Column(String(20), nullable=False, default="active")
    last_login_at = Column(DateTime, nullable=True)

    role = Column(user_role_enum, nullable=False, server_default="user")
    favorites = relationship("Favorite", back_populates="user")
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )

    tokens = relationship(
        "UserToken", back_populates="user", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_user_email_lower", func.lower(email), unique=True),
    )



# app/models/users.py 중 일부

class UserToken(Base):
    __tablename__ = "user_token"

    user_token_id = Column(BigInteger, primary_key=True, autoincrement=True)

    user_id = Column(
        BigInteger,
        ForeignKey("user.user_id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    # ↓ VARCHAR(255)에 맞추기
    refresh_token_hash = Column(String(255), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    revoked_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )

    user = relationship("User", back_populates="tokens")

    __table_args__ = (
        Index("ix_user_token_user_id", "user_id"),
        UniqueConstraint(
            "user_id", "refresh_token_hash", name="uq_user_token_user_refresh"
        ),
    )
