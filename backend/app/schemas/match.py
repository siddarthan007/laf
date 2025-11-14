from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.match import MatchStatus
from app.schemas.item import ItemReportResponse


class MatchBase(BaseModel):
    id: UUID
    lost_item_id: UUID
    found_item_id: UUID
    loser_id: UUID
    finder_id: UUID
    confidence_score: float
    match_status: MatchStatus
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MatchRead(MatchBase):
    lost_item: ItemReportResponse
    found_item: ItemReportResponse


class MatchDecisionResponse(BaseModel):
    match: MatchRead
    message: str
    contact_shared_with_loser: Optional[dict[str, str]]
    contact_shared_with_finder: Optional[dict[str, str]]

