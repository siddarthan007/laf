from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.models import Match, MatchStatus
from app.schemas.match import MatchDecisionResponse, MatchRead
from app.services.items import get_matches_for_user
from app.services.matching import approve_match, reject_match
from app.services.notifications import notify_match_resolution
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/matches", tags=["matches"])


@router.get("/my_matches", response_model=list[MatchRead])
async def my_matches(
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
) -> list[MatchRead]:
    matches = await get_matches_for_user(session, user=current_user)
    return [MatchRead.model_validate(match) for match in matches]


def _ensure_pending_match(match: Match | None) -> Match:
    if match is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Match not found")
    if match.match_status != MatchStatus.PENDING:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Match already resolved")
    return match


@router.post("/{match_id}/approve", response_model=MatchDecisionResponse)
async def approve_match_endpoint(
    match_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
) -> MatchDecisionResponse:
    statement = select(Match).where(Match.id == match_id)
    match = _ensure_pending_match((await session.execute(statement)).scalar_one_or_none())

    try:
        match, loser_contact, finder_contact = await approve_match(session, match=match, acting_user=current_user)
    except PermissionError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to approve this match") from None

    await notify_match_resolution(match=match, loser_contact=loser_contact, finder_contact=finder_contact)

    await session.refresh(match, attribute_names=["lost_item", "found_item"])
    return MatchDecisionResponse(
        match=MatchRead.model_validate(match),
        message="Match approved and items archived",
        contact_shared_with_loser=loser_contact,
        contact_shared_with_finder=finder_contact,
    )


@router.post("/{match_id}/reject", response_model=MatchRead)
async def reject_match_endpoint(
    match_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
) -> MatchRead:
    statement = select(Match).where(Match.id == match_id)
    match = _ensure_pending_match((await session.execute(statement)).scalar_one_or_none())

    try:
        match = await reject_match(session, match=match, acting_user=current_user)
    except PermissionError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to reject this match") from None

    await session.refresh(match, attribute_names=["lost_item", "found_item"])
    return MatchRead.model_validate(match)


