"""Authentication routes: register, login, refresh, profile."""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.security import create_access_token, create_refresh_token, hash_password, verify_password
from app.models.user import User, UserRole
from app.core.rate_limit import enforce_rate_limit, limit_auth_source
from app.schemas.schemas import UserRegister, UserLogin, UserResponse, TokenResponse, RefreshRequest

router = APIRouter()
_dummy_hash = hash_password(uuid.uuid4().hex)


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(limit_auth_source)])
async def register(data: UserRegister, db: AsyncSession = Depends(get_db)):
    """Register a new user account."""
    existing = await db.execute(select(User).where((User.email == data.email) | (User.username == data.username)))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email or username already exists")

    user = User(
        email=data.email,
        username=data.username,
        hashed_password=hash_password(data.password),
        full_name=data.full_name,
        phone=data.phone,
        role=UserRole.CITIZEN,
        organization=data.organization,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


@router.post("/login", response_model=TokenResponse, dependencies=[Depends(limit_auth_source)])
async def login(data: UserLogin, db: AsyncSession = Depends(get_db)):
    """Login and receive JWT access + refresh tokens."""
    await enforce_rate_limit("login-account", data.email.strip().lower(), 20, 300)
    result = await db.execute(select(User).where(User.email == data.email, User.is_deleted == False))
    user = result.scalar_one_or_none()

    valid_password = verify_password(data.password, user.hashed_password if user else _dummy_hash)
    if not user or not valid_password:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is deactivated")

    user.last_login_at = datetime.now(timezone.utc)
    token_data = {"sub": str(user.id), "role": user.role}

    return TokenResponse(
        access_token=create_access_token(token_data),
        refresh_token=create_refresh_token(token_data),
    )


@router.post("/refresh", response_model=TokenResponse, dependencies=[Depends(limit_auth_source)])
async def refresh_token(data: RefreshRequest, db: AsyncSession = Depends(get_db)):
    """Refresh an expired access token using a valid refresh token."""
    from app.core.security import decode_token
    payload = decode_token(data.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    try:
        user_id = uuid.UUID(payload.get("sub", ""))
    except (ValueError, TypeError, AttributeError):
        raise HTTPException(status_code=401, detail="Invalid refresh token") from None
    result = await db.execute(select(User).where(User.id == user_id, User.is_deleted == False))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")

    token_data = {"sub": str(user.id), "role": user.role}
    return TokenResponse(
        access_token=create_access_token(token_data),
        refresh_token=create_refresh_token(token_data),
    )


@router.get("/me", response_model=UserResponse)
async def get_profile(current_user: User = Depends(get_current_user)):
    """Get the current authenticated user's profile."""
    return current_user
