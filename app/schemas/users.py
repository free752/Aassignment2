
from datetime import datetime, date
from typing import Optional, Literal

from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    email: EmailStr
    name: str
    is_korean: bool = True
    address: Optional[str] = None
    phone_number: Optional[str] = None
    birth_date: Optional[date] = None
    gender: Optional[Literal["male", "female"]] = None
    profile: Optional[str] = None


class UserCreate(UserBase):
    password: str  # 나중에 길이/패턴 검증 추가 예정


class UserRead(UserBase):
    user_id: int
    status: str
    role: str
    email_verified_at: Optional[datetime] = None
    last_login_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
class UserUpdateFull(BaseModel):
    name: str
    is_korean: bool
    address: Optional[str] = None
    phone_number: Optional[str] = None
    birth_date: Optional[date] = None
    gender: Optional[Literal["male", "female"]] = None
    profile: Optional[str] = None

class UserUpdatePartial(BaseModel):
    name: Optional[str] = None
    is_korean: Optional[bool] = None
    address: Optional[str] = None
    phone_number: Optional[str] = None
    birth_date: Optional[date] = None
    gender: Optional[Literal["male", "female"]] = None
    profile: Optional[str] = None

    class Config:
        extra = "forbid"