from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.schemas.user import UserRead, UserUpdate
from app.services.users import update_user
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserRead)
async def read_current_user(current_user=Depends(get_current_user)) -> UserRead:
    return UserRead.model_validate(current_user)


@router.patch("/me", response_model=UserRead)
async def update_current_user(
    payload: UserUpdate,
    current_user=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> UserRead:
    updated_user = await update_user(session, current_user, payload)
    return UserRead.model_validate(updated_user)


