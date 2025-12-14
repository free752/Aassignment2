from typing import Optional
from pydantic import BaseModel

# 공통 필드 -------------------------
class AuthorBase(BaseModel):
    name: str
    profile: Optional[str] = None


# 생성 요청용 -----------------------
class AuthorCreate(AuthorBase):
    """작가 생성에 사용하는 스키마"""
    pass


# 전체 수정( PUT ) -------------------
class AuthorUpdateFull(AuthorBase):
    """작가 전체 수정용 (PUT) – name, profile 둘 다 항상 들어와야 함"""
    pass


# 부분 수정( PATCH ) -----------------
class AuthorUpdatePartial(BaseModel):
    """작가 부분 수정용 (PATCH) – 일부 필드만 들어와도 됨"""
    name: Optional[str] = None
    profile: Optional[str] = None


# 응답용 ----------------------------
class AuthorRead(AuthorBase):
    author_id: int

    class Config:
        from_attributes = True  # SQLAlchemy ORM 객체 -> 응답 변환