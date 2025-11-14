from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

from fastapi import BackgroundTasks, HTTPException, UploadFile, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import get_settings
from app.models import Item, ItemStatus, Match, MatchStatus, User
from app.schemas.item import ItemListFilters
from app.services.embeddings import embedding_service
from app.tasks.matching import schedule_matching
from app.utils.files import read_validated_upload, save_upload_file

logger = logging.getLogger(__name__)

settings = get_settings()


@dataclass(slots=True)
class ReportItemPayload:
    description: str
    location: str
    status: ItemStatus
    image_file: Optional[UploadFile] = None
    is_admin_report: bool = False


async def _persist_item(
    session: AsyncSession,
    *,
    reporter: User,
    payload: ReportItemPayload,
) -> Item:
    if payload.status == ItemStatus.FOUND and payload.image_file is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Found items require an image")

    image_bytes: bytes | None = None
    if payload.image_file is not None:
        image_bytes = await read_validated_upload(
            payload.image_file,
            allowed_mimetypes=settings.upload_allowed_mimetypes,
            max_bytes=settings.upload_max_bytes,
        )

    embedding_bundle = await embedding_service.generate_bundle(
        description=payload.description,
        image_bytes=image_bytes,
    )

    image_url: str | None = None
    if payload.image_file is not None and image_bytes is not None:
        stored_path = await save_upload_file(
            payload.image_file,
            settings.static_upload_dir,
            file_bytes=image_bytes,
        )
        image_url = f"/{stored_path.as_posix()}"

    item = Item(
        reported_by_user_id=reporter.id,
        status=payload.status,
        description=payload.description,
        location=payload.location,
        image_url=image_url,
        description_vector=embedding_bundle.description_vector,
        description_clip_vector=embedding_bundle.description_clip_vector,
        image_vector=embedding_bundle.image_vector,
        is_admin_report=payload.is_admin_report,
    )
    session.add(item)
    await session.flush()
    return item


async def report_item(
    session: AsyncSession,
    *,
    reporter: User,
    payload: ReportItemPayload,
    background_tasks: BackgroundTasks,
) -> Item:
    """Persist an item report and schedule matching."""

    item = await _persist_item(session, reporter=reporter, payload=payload)
    await session.commit()

    logger.info(f"Scheduling matching for item {item.id} (status: {item.status}, description: {item.description[:50]}...)")
    background_tasks.add_task(schedule_matching, item.id)
    logger.info(f"Background task scheduled for item {item.id}")
    return item


async def resolve_item(session: AsyncSession, *, item: Item) -> Item:
    """Archive an item manually when the user resolves it."""

    item.is_active = False
    session.add(item)
    await session.commit()
    await session.refresh(item)
    return item


async def list_found_items(
    session: AsyncSession,
    *,
    filters: ItemListFilters,
) -> list[Item]:
    statement = select(Item).where(
        Item.status == ItemStatus.FOUND,
        Item.is_active.is_(True),
    )

    if filters.location:
        statement = statement.where(Item.location.ilike(f"%{filters.location}%"))
    if filters.date_after:
        statement = statement.where(Item.reported_at >= filters.date_after)
    if filters.date_before:
        statement = statement.where(Item.reported_at <= filters.date_before)

    statement = statement.order_by(Item.reported_at.desc())
    results = await session.execute(statement)
    return list(results.scalars().all())


async def get_matches_for_user(session: AsyncSession, *, user: User) -> list[Match]:
    """Get all matches where the user is either the loser or finder (including PENDING, APPROVED, and REJECTED)."""
    statement = (
        select(Match)
        .where(
            or_(
                Match.loser_id == user.id,
                Match.finder_id == user.id
            )
        )
        .order_by(Match.created_at.desc())
    )

    matches = list((await session.execute(statement)).scalars().all())
    for match in matches:
        await session.refresh(match, attribute_names=["lost_item", "found_item"])
    return matches


