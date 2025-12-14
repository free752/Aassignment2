from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import (
    verify_password,
    hash_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.core.config import get_settings
from app.db import get_db
from datetime import datetime, timedelta, timezone

from app.models.users import User, UserToken

from app.schemas.auth import (
    LoginRequest,
    TokenPair,
    RefreshRequest,
    TokenPayload,
    LogoutRequest,
)
from fastapi.security import OAuth2PasswordRequestForm

settings = get_settings()

router = APIRouter(
    prefix="/api/v1/auth",
    tags=["auth"],
)


def _save_refresh_token(db: Session, user: User, refresh_token: str) -> None:
    """리프레시 토큰을 해시해서 DB에 저장 (user_token 테이블)."""
    token_hash = hash_password(refresh_token)
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    user_token = UserToken(
        user_id=user.user_id,
        refresh_token_hash=token_hash,
        expires_at=expires_at,
    )
    db.add(user_token)
    db.commit()

def _find_valid_refresh_token(
    db: Session,
    user: User,
    refresh_token: str,
) -> UserToken:
    """DB에 저장된 해시 중에서, 이 refresh_token과 일치하고 아직 유효한 토큰 찾기."""
    now = datetime.now(timezone.utc)

    candidates = (
        db.query(UserToken)
        .filter(
            UserToken.user_id == user.user_id,
            UserToken.revoked_at.is_(None),
            UserToken.expires_at > now,
        )
        .all()
    )

    for token_row in candidates:
        # bcrypt 해시 비교 재사용
        if verify_password(refresh_token, token_row.refresh_token_hash):
            return token_row

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired refresh token",
    )

@router.post(path="/login", response_model=TokenPair)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    email = form_data.username
    password = form_data.password

    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email or password",
        )

    if not verify_password(password, user.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email or password",
        )

    # 아래는 기존 토큰 생성 / 저장 로직 그대로 두면 됨
    claims = {"sub": str(user.user_id), "role": user.role}
    access_token = create_access_token(claims)
    refresh_token = create_refresh_token(claims)
    _save_refresh_token(db, user, refresh_token)

    return TokenPair(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
    )

@router.post("/refresh", response_model=TokenPair)
def refresh_token(
    payload: RefreshRequest,
    db: Session = Depends(get_db),
):
    # 1) 토큰 구조/서명 검증
    try:
        decoded = decode_token(payload.refresh_token)
        token_data = TokenPayload(**decoded)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    # 2) 유저 조회
    user = db.query(User).filter(User.user_id == int(token_data.sub)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found for this token",
        )

    # 3) DB에 저장된 유효한 refresh token인지 확인
    token_row = _find_valid_refresh_token(db, user, payload.refresh_token)

    # 4) 이전 토큰 revoke
    now = datetime.now(timezone.utc)
    token_row.revoked_at = now
    db.add(token_row)

    # 5) 새 토큰 발급
    claims = {"sub": str(user.user_id), "role": user.role}
    new_access = create_access_token(claims)
    new_refresh = create_refresh_token(claims)

    # 6) 새 refresh 토큰 저장
    _save_refresh_token(db, user, new_refresh)

    return TokenPair(
        access_token=new_access,
        refresh_token=new_refresh,
    )

@router.post("/logout")
def logout(
    payload: LogoutRequest,
    db: Session = Depends(get_db),
):
    # 1) 리프레시 토큰 decode
    try:
        decoded = decode_token(payload.refresh_token)
        token_data = TokenPayload(**decoded)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    user = db.query(User).filter(User.user_id == int(token_data.sub)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found for this token",
        )

    # 2) 해당 리프레시 토큰 row 찾기
    token_row = _find_valid_refresh_token(db, user, payload.refresh_token)

    # 3) revoke 처리
    now = datetime.now(timezone.utc)
    token_row.revoked_at = now
    db.add(token_row)
    db.commit()

    return {"message": "Logged out"}
