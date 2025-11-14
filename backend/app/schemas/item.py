from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.item import ItemStatus
from app.schemas.user import UserSummary


class ItemBase(BaseModel):
    id: UUID
    status: ItemStatus
    description: str
    location: str
    image_url: Optional[str]
    is_active: bool
    is_admin_report: bool
    has_match_found: bool
    reported_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ItemReportResponse(ItemBase):
    reported_by: UserSummary


class ItemListFilters(BaseModel):
    location: Optional[str] = Field(default=None)
    date_after: Optional[datetime] = Field(default=None)
    date_before: Optional[datetime] = Field(default=None)
    status: Optional[ItemStatus] = Field(default=None)


class ItemSearchResponse(ItemReportResponse):
    similarity_score: Optional[float] = None


