from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.schemas.auth import LoginRequest, RefreshTokenRequest, Token
from app.schemas.user import UserCreate, UserRead
from app.services.users import authenticate_user, create_user
from app.utils.security import create_access_token, create_refresh_token, decode_token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserRead, status_code=201)
async def register_user(payload: UserCreate, session: AsyncSession = Depends(get_session)) -> UserRead:
    user = await create_user(session, payload)
    return UserRead.model_validate(user)


@router.post("/login", response_model=Token)
async def login(payload: LoginRequest, session: AsyncSession = Depends(get_session)) -> Token:
    user = await authenticate_user(session, payload.email, payload.password)
    return Token(
        access_token=create_access_token(subject=user.id),
        refresh_token=create_refresh_token(subject=user.id),
    )


@router.post("/refresh", response_model=Token)
async def refresh_tokens(payload: RefreshTokenRequest) -> Token:
    try:
        token_payload = decode_token(payload.refresh_token)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token") from None

    return Token(
        access_token=create_access_token(subject=token_payload.sub),
        refresh_token=create_refresh_token(subject=token_payload.sub),
    )

