from datetime import datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy import func, or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.models import Item, ItemStatus, Match, MatchStatus, User, UserRole
from app.schemas.item import ItemListFilters, ItemReportResponse, ItemSearchResponse
from app.schemas.match import MatchRead
from app.schemas.user import UserRead
from app.services.items import ReportItemPayload, report_item
from app.services.search import search_items_admin
from app.services.embeddings import embedding_service
from app.utils.dependencies import get_current_admin

router = APIRouter(prefix="/admin", tags=["admin"])


async def _resolve_user(session: AsyncSession, identifier: str) -> User:
    statement = select(User).where(or_(User.email == identifier, User.roll_number == identifier))
    result = await session.execute(statement)
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.post("/report_on_behalf", response_model=ItemReportResponse, status_code=201)
async def report_on_behalf(
    background_tasks: BackgroundTasks,
    user_identifier: str = Form(...),
    item_status: ItemStatus = Form(...),
    description: str = Form(...),
    location: str = Form(...),
    image: UploadFile | None = File(default=None),
    session: AsyncSession = Depends(get_session),
    current_admin=Depends(get_current_admin),
) -> ItemReportResponse:
    target_user = await _resolve_user(session, user_identifier)
    item = await report_item(
        session,
        reporter=target_user,
        payload=ReportItemPayload(
            description=description,
            location=location,
            status=item_status,
            image_file=image,
            is_admin_report=True,
        ),
        background_tasks=background_tasks,
    )
    await session.refresh(item, attribute_names=["reported_by"])
    return ItemReportResponse.model_validate(item)


@router.post("/report_office_item", response_model=ItemReportResponse, status_code=201)
async def report_office_found_item(
    background_tasks: BackgroundTasks,
    item_status: ItemStatus = Form(...),
    description: str = Form(...),
    location: str = Form(...),
    image: UploadFile = File(...),
    session: AsyncSession = Depends(get_session),
    current_admin=Depends(get_current_admin),
) -> ItemReportResponse:
    if item_status != ItemStatus.FOUND:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Office can only report found items")

    item = await report_item(
        session,
        reporter=current_admin,
        payload=ReportItemPayload(
            description=description,
            location=location,
            status=item_status,
            image_file=image,
            is_admin_report=True,
        ),
        background_tasks=background_tasks,
    )
    await session.refresh(item, attribute_names=["reported_by"])
    return ItemReportResponse.model_validate(item)


@router.get("/dashboard/analytics")
async def admin_analytics(
    session: AsyncSession = Depends(get_session),
    current_admin=Depends(get_current_admin),
) -> dict[str, Any]:
    total_users = await session.scalar(select(func.count(User.id)))
    total_active_lost = await session.scalar(
        select(func.count(Item.id)).where(Item.status == ItemStatus.LOST, Item.is_active.is_(True))
    )
    total_active_found = await session.scalar(
        select(func.count(Item.id)).where(Item.status == ItemStatus.FOUND, Item.is_active.is_(True))
    )
    total_resolved = await session.scalar(select(func.count(Item.id)).where(Item.is_active.is_(False)))
    total_matches_pending = await session.scalar(
        select(func.count(Match.id)).where(Match.match_status == MatchStatus.PENDING)
    )
    total_matches_approved = await session.scalar(
        select(func.count(Match.id)).where(Match.match_status == MatchStatus.APPROVED)
    )

    trend_statement = (
        select(
            func.date_trunc("day", Item.reported_at).label("day"),
            func.count().label("count"),
            Item.status,
        )
        .where(Item.reported_at >= func.now() - text("interval '30 days'"))
        .group_by("day", Item.status)
        .order_by("day")
    )
    trend_rows = await session.execute(trend_statement)

    daily_trends: dict[str, dict[str, int]] = {}
    for day, count, status_value in trend_rows:
        key = day.date().isoformat()
        status_key = status_value.value if isinstance(status_value, ItemStatus) else str(status_value)
        bucket = daily_trends.setdefault(key, {"LOST": 0, "FOUND": 0})
        bucket[status_key] = count

    return {
        "totals": {
            "users": total_users or 0,
            "lost_active": total_active_lost or 0,
            "found_active": total_active_found or 0,
            "resolved": total_resolved or 0,
            "matches_pending": total_matches_pending or 0,
            "matches_approved": total_matches_approved or 0,
        },
        "daily_reports_last_30_days": daily_trends,
    }


@router.get("/dashboard/users", response_model=list[UserRead])
async def admin_users_table(
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0),
    session: AsyncSession = Depends(get_session),
    current_admin=Depends(get_current_admin),
) -> list[UserRead]:
    statement = select(User).order_by(User.created_at.desc()).offset(offset).limit(limit)
    users = list((await session.execute(statement)).scalars().all())
    return [UserRead.model_validate(user) for user in users]


@router.get("/dashboard/items", response_model=list[ItemSearchResponse])
async def admin_items_table(
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0),
    status_filter: ItemStatus | None = Query(default=None, alias="status"),
    include_archived: bool = Query(default=True),
    q: str | None = Query(default=None, min_length=2),
    include_matches: bool = Query(default=True),
    session: AsyncSession = Depends(get_session),
    current_admin=Depends(get_current_admin),
) -> list[ItemSearchResponse]:
    if q:
        status_str = status_filter.value if status_filter else None
        search_query = q.strip()
        try:
            query_vector = await embedding_service.encode_query(search_query)
        except RuntimeError:
            query_vector = None
        
        results = await search_items_admin(
            session,
            query=search_query,
            query_vector=query_vector,
            status_filter=status_str,
            include_archived=include_archived,
            include_matches=include_matches,
            limit=limit,
            fuzzy_weight=0.4,
            vector_weight=0.6,
            min_score=0.3,
        )
        
        response: list[ItemSearchResponse] = []
        for item, score in results:
            await session.refresh(item, attribute_names=["reported_by"])
            model = ItemSearchResponse.model_validate(item)
            model.similarity_score = score
            response.append(model)
        return response

    filters = ItemListFilters(status=status_filter)
    statement = select(Item)
    if filters.status:
        statement = statement.where(Item.status == filters.status)
    if not include_archived:
        statement = statement.where(Item.is_active.is_(True))

    statement = statement.order_by(Item.reported_at.desc()).offset(offset).limit(limit)
    items = list((await session.execute(statement)).scalars().all())
    response: list[ItemSearchResponse] = []
    for item in items:
        await session.refresh(item, attribute_names=["reported_by"])
        response.append(ItemSearchResponse.model_validate(item))
    return response


@router.get("/dashboard/matches", response_model=list[MatchRead])
async def admin_matches_table(
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0),
    status_filter: MatchStatus | None = Query(default=None, alias="status"),
    session: AsyncSession = Depends(get_session),
    current_admin=Depends(get_current_admin),
) -> list[MatchRead]:
    statement = select(Match).order_by(Match.created_at.desc())
    if status_filter:
        statement = statement.where(Match.match_status == status_filter)
    statement = statement.offset(offset).limit(limit)
    matches = list((await session.execute(statement)).scalars().all())
    for match in matches:
        await session.refresh(match, attribute_names=["lost_item", "found_item"])
    return [MatchRead.model_validate(match) for match in matches]

