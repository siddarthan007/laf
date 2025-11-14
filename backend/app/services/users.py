from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User, UserRole
from app.schemas.user import UserCreate, UserUpdate
from app.utils.security import hash_password, verify_password


async def get_user_by_email(session: AsyncSession, email: str) -> User | None:
    statement = select(User).where(User.email == email)
    result = await session.execute(statement)
    return result.scalar_one_or_none()


async def create_user(session: AsyncSession, payload: UserCreate, *, role: UserRole = UserRole.USER) -> User:
    if await get_user_by_email(session, payload.email):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    statement = select(User).where(User.roll_number == payload.roll_number)
    if (await session.execute(statement)).scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Roll number already registered")

    user = User(
        name=payload.name,
        email=payload.email,
        hashed_password=hash_password(payload.password),
        roll_number=payload.roll_number,
        hostel=payload.hostel,
        contact_number=payload.contact_number,
        role=role,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def authenticate_user(session: AsyncSession, email: str, password: str) -> User:
    user = await get_user_by_email(session, email)
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")
    return user


async def update_user(session: AsyncSession, user: User, payload: UserUpdate) -> User:
    """Update user information. Only updates fields that are provided."""
    if payload.email and payload.email != user.email:
        if await get_user_by_email(session, payload.email):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
        user.email = payload.email

    if payload.name is not None:
        user.name = payload.name

    if payload.hostel is not None:
        user.hostel = payload.hostel

    if payload.contact_number is not None:
        user.contact_number = payload.contact_number

    if payload.password is not None:
        user.hashed_password = hash_password(payload.password)

    await session.commit()
    await session.refresh(user)
    return user


