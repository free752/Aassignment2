# app/api/users.py
from typing import Optional
from app.schemas.common import UserListPage
from typing import List
import math
from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from pydantic import BaseModel
from datetime import datetime

from app.models.users import User
from app.schemas.users import UserCreate, UserRead, UserUpdateFull, UserUpdatePartial
from app.core.security import hash_password
from app.core.security import get_current_admin
from sqlalchemy.orm import Session
from app.db import get_db
from app.core.security import get_current_user



router = APIRouter(prefix="/api/v1/users", tags=["users"])


@router.get("/me", response_model=UserRead)
def get_me(
    current_user: User = Depends(get_current_user),
):
    """현재 로그인한 사용자 정보 조회"""
    return current_user

@router.patch("/me", response_model=UserRead)
def update_me_partial(
    payload: UserUpdatePartial,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user = db.query(User).filter(User.user_id == current_user.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # ★ 핵심: 클라이언트가 실제로 보낸 필드만 뽑기
    update_data = payload.model_dump(exclude_unset=True)

    # 보낸 필드만 반영
    for key, value in update_data.items():
        setattr(user, key, value)

    user.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(user)
    return user

@router.post(
    "",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
)
def create_user(payload: UserCreate, db: Session = Depends(get_db)):
    # 이메일 중복 체크
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        # 나중에 에러 포맷 통일할 때 수정
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already exists",
        )

    user = User(
        email=payload.email,
        password=hash_password(payload.password),
        name=payload.name,
        is_korean=payload.is_korean,
        address=payload.address,
        phone_number=payload.phone_number,
        birth_date=payload.birth_date,
        gender=payload.gender,
        profile=payload.profile,
        role="user",
        status="active",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user




@router.put("/me", response_model=UserRead)
def update_me_full(
    payload: UserUpdateFull,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user = db.query(User).filter(User.user_id == current_user.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # 전체 필드를 덮어쓰기
    user.name = payload.name
    user.is_korean = payload.is_korean
    user.address = payload.address
    user.phone_number = payload.phone_number
    user.birth_date = payload.birth_date
    user.gender = payload.gender
    user.profile = payload.profile
    user.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(user)
    return user

@router.delete(
    "/me",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="내 계정 비활성화(soft delete)",
)
def deactivate_me(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # 이미 blocked면 멱등 처리
    if current_user.status == "blocked":
        return

    current_user.status = "blocked"
    current_user.updated_at = datetime.utcnow()

    db.add(current_user)
    db.commit()
    # 204라서 바디 없이 리턴
    return

@router.delete(
    "/me/permanent",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="내 계정 완전 삭제(hard delete)",
)
def delete_me_permanent(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    db.delete(current_user)
    db.commit()
    return

@router.get("", response_model=UserListPage)
def list_users(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
    page: int = Query(0, ge=0),
    size: int = Query(20, ge=1, le=100),
    keyword: Optional[str] = Query(None),
    sort: str = Query("created_at,desc"),  # 추가
):
    query = db.query(User)

    if keyword:
        like = f"%{keyword}%"
        query = query.filter((User.name.ilike(like)) | (User.email.ilike(like)))

    field, direction = (sort.split(",") + ["desc"])[:2]
    direction = direction.lower()
    sort_map = {
        "created_at": User.created_at,
        "user_id": User.user_id,
        "name": User.name,
        "email": User.email,
        "status": User.status,
        "role": User.role,
    }
    col = sort_map.get(field, User.created_at)
    query = query.order_by(col.asc() if direction == "asc" else col.desc())


    items = query.offset(page * size).limit(size).all()
    total = query.order_by(None).count()
    total_pages = (total + size - 1) // size

    return {
        "content": items,
        "page": page,
        "size": size,
        "totalElements": total,
        "totalPages": total_pages,
        "sort": sort,
    }


# 2) 특정 사용자 상세 조회 (ADMIN)
@router.get("/{user_id}", response_model=UserRead, summary="특정 사용자 조회 (ADMIN)")
def get_user_detail(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user


# 3) 사용자 상태/권한 변경 (ADMIN)
class UserAdminUpdateStatus(BaseModel):
    status: Optional[str] = None   # "active", "blocked"
    role: Optional[str] = None     # "user", "admin"

@router.patch(
    "/{user_id}/status",
    response_model=UserRead,
    summary="사용자 상태/권한 변경 (ADMIN)",
)
def update_user_status(
    user_id: int,
    payload: UserAdminUpdateStatus,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    data = payload.model_dump(exclude_unset=True)
    if "status" in data:
        user.status = data["status"]
    if "role" in data:
        user.role = data["role"]

    db.commit()
    db.refresh(user)
    return user