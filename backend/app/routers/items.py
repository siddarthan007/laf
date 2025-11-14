from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import get_settings
from app.db.session import get_session
from app.models import Item, ItemStatus, Match, MatchStatus
from app.schemas.item import ItemListFilters, ItemReportResponse, ItemSearchResponse
from app.services.embeddings import embedding_service
from app.services.items import ReportItemPayload, list_found_items, report_item, resolve_item
from app.services.search import search_items_hybrid
from app.utils.dependencies import get_current_user
from app.utils.files import delete_upload_file

router = APIRouter(prefix="/items", tags=["items"])


@router.post("/report_lost", response_model=ItemReportResponse, status_code=201)
async def report_lost_item(
    background_tasks: BackgroundTasks,
    description: str = Form(...),
    location: str = Form(...),
    image: UploadFile | None = File(default=None),
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
) -> ItemReportResponse:
    item = await report_item(
        session,
        reporter=current_user,
        payload=ReportItemPayload(
            description=description,
            location=location,
            status=ItemStatus.LOST,
            image_file=image,
        ),
        background_tasks=background_tasks,
    )
    await session.refresh(item, attribute_names=["reported_by"])
    return ItemReportResponse.model_validate(item)


@router.post("/report_found", response_model=ItemReportResponse, status_code=201)
async def report_found_item(
    background_tasks: BackgroundTasks,
    description: str = Form(...),
    location: str = Form(...),
    image: UploadFile = File(...),
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
) -> ItemReportResponse:
    item = await report_item(
        session,
        reporter=current_user,
        payload=ReportItemPayload(
            description=description,
            location=location,
            status=ItemStatus.FOUND,
            image_file=image,
        ),
        background_tasks=background_tasks,
    )
    await session.refresh(item, attribute_names=["reported_by"])
    return ItemReportResponse.model_validate(item)


@router.get("/all_found_items", response_model=list[ItemReportResponse])
async def list_active_found_items(
    location: str | None = Query(default=None),
    date_after: datetime | None = Query(default=None),
    date_before: datetime | None = Query(default=None),
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
) -> list[ItemReportResponse]:
    filters = ItemListFilters(location=location, date_after=date_after, date_before=date_before)
    items = await list_found_items(session, filters=filters)
    for item in items:
        await session.refresh(item, attribute_names=["reported_by"])
    return [ItemReportResponse.model_validate(item) for item in items]


@router.post("/{item_id}/resolve", response_model=ItemReportResponse)
async def resolve_reported_item(
    item_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
) -> ItemReportResponse:
    """Resolve a lost item. Only the owner of a LOST item can resolve it. Found items are archived automatically when matches are approved."""
    item = await session.get(Item, item_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    if item.reported_by_user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only resolve your own items")
    if item.status != ItemStatus.LOST:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only lost items can be resolved. Found items are archived automatically when matches are approved."
        )

    item = await resolve_item(session, item=item)
    await session.refresh(item, attribute_names=["reported_by"])
    return ItemReportResponse.model_validate(item)


@router.get("/my_items", response_model=list[ItemReportResponse])
async def get_my_items(
    status_filter: ItemStatus | None = Query(default=None, alias="status"),
    include_archived: bool = Query(default=False),
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
) -> list[ItemReportResponse]:
    """Get all items reported by the current user."""
    filters = [Item.reported_by_user_id == current_user.id]
    
    if status_filter:
        filters.append(Item.status == status_filter)
    
    if not include_archived:
        filters.append(Item.is_active.is_(True))

    statement = select(Item).where(and_(*filters)).order_by(Item.reported_at.desc())

    items = list((await session.execute(statement)).scalars().all())
    for item in items:
        await session.refresh(item, attribute_names=["reported_by"])
    return [ItemReportResponse.model_validate(item) for item in items]


@router.delete("/{item_id}")
async def delete_item(
    item_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
) -> dict[str, str]:
    """Delete an item. Users can only delete their own items."""
    item = await session.get(Item, item_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    if item.reported_by_user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only delete your own items")
    
    # Check if item has approved matches
    approved_match = await session.scalar(
        select(Match).where(
            or_(
                Match.lost_item_id == item_id,
                Match.found_item_id == item_id
            ),
            Match.match_status == MatchStatus.APPROVED
        )
    )
    if approved_match:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete item with approved matches. Please resolve it instead."
        )
    
    # Delete associated image file before deleting the item
    settings = get_settings()
    if item.image_url:
        await delete_upload_file(item.image_url, settings.static_upload_dir)
    
    await session.delete(item)
    await session.commit()
    return {"message": "Item deleted successfully"}


@router.get("/search", response_model=list[ItemSearchResponse])
async def search_items(
    q: str = Query(..., min_length=2),
    status_filter: ItemStatus | None = Query(default=None, alias="status"),
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
) -> list[ItemSearchResponse]:
    """
    Search items using hybrid fuzzy matching and vector similarity search.
    
    Combines:
    - Fuzzy string matching (rapidfuzz) for typo tolerance and partial matches
    - Vector similarity search (sentence-transformers) for semantic understanding
    
    The hybrid approach provides both exact/partial matches and semantically
    similar results, giving the best of both worlds.
    """
    status_str = status_filter.value if status_filter else None
    
    # Generate query embedding for vector similarity search
    # This enables semantic search - finding items that are semantically
    # similar even if they don't contain exact keyword matches
    try:
        query_vector = await embedding_service.encode_query(q)
    except RuntimeError as e:
        # If embedding service is not loaded, fall back to fuzzy-only search
        # This should not happen in production, but provides graceful degradation
        query_vector = None
    
    # Use hybrid search with balanced weights
    # 40% fuzzy (for exact/partial matches) + 60% vector (for semantic similarity)
    # This can be adjusted based on performance requirements
    results = await search_items_hybrid(
        session,
        query=q,
        query_vector=query_vector,
        status_filter=status_str,
        include_archived=False,
        limit=50,
        fuzzy_weight=0.4,  # 40% weight for fuzzy matching
        vector_weight=0.6,  # 60% weight for semantic similarity
        min_score=0.3,
    )
    
    response: list[ItemSearchResponse] = []
    for item, score in results:
        await session.refresh(item, attribute_names=["reported_by"])
        model = ItemSearchResponse.model_validate(item)
        model.similarity_score = score
        response.append(model)
    return response

