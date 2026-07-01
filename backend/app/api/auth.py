from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import User
from app.schemas import AgentSignUpRequest, AuthResponse, LoginRequest, RenterSignUpRequest, UserResponse
from app.services.auth import create_access_token, get_current_user, hash_password, verify_password

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/agent/signup", response_model=AuthResponse)
async def agent_signup(req: AgentSignUpRequest, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(User).where(User.email == req.email.lower().strip()))
    if existing.scalar_one_or_none():
        raise HTTPException(400, "An account with this email already exists")

    user = User(
        email=req.email.lower().strip(),
        password_hash=hash_password(req.password),
        role="agent",
        full_name=req.full_name.strip(),
        phone=req.phone.strip(),
        agency_name=req.agency_name.strip(),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return AuthResponse(access_token=create_access_token(user), user=UserResponse.model_validate(user))


@router.post("/renter/signup", response_model=AuthResponse)
async def renter_signup(req: RenterSignUpRequest, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(User).where(User.email == req.email.lower().strip()))
    if existing.scalar_one_or_none():
        raise HTTPException(400, "An account with this email already exists")

    user = User(
        email=req.email.lower().strip(),
        password_hash=hash_password(req.password),
        role="renter",
        full_name=req.full_name.strip(),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return AuthResponse(access_token=create_access_token(user), user=UserResponse.model_validate(user))


@router.post("/login", response_model=AuthResponse)
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == req.email.lower().strip()))
    user = result.scalar_one_or_none()
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(401, "Invalid email or password")

    return AuthResponse(access_token=create_access_token(user), user=UserResponse.model_validate(user))


@router.get("/me", response_model=UserResponse)
async def me(user: User = Depends(get_current_user)):
    return user
