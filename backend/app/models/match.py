import enum
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum as SQLEnum, Float, ForeignKey, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base

if TYPE_CHECKING:
    from app.models.item import Item
    from app.models.user import User


class MatchStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class Match(Base):
    """Represents a potential match between a lost and found item."""

    __tablename__ = "matches"
    __table_args__ = (
        UniqueConstraint("lost_item_id", "found_item_id", name="uq_match_lost_found"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lost_item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("items.id", ondelete="CASCADE"), nullable=False, index=True
    )
    found_item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("items.id", ondelete="CASCADE"), nullable=False, index=True
    )
    loser_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    finder_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False)
    match_status: Mapped[MatchStatus] = mapped_column(
        SQLEnum(MatchStatus, name="match_status"),
        nullable=False,
        default=MatchStatus.PENDING,
        server_default=MatchStatus.PENDING.value,
    )
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    lost_item: Mapped["Item"] = relationship(
        back_populates="matches_as_lost",
        foreign_keys=[lost_item_id],
        lazy="joined",
    )
    found_item: Mapped["Item"] = relationship(
        back_populates="matches_as_found",
        foreign_keys=[found_item_id],
        lazy="joined",
    )

    loser: Mapped["User"] = relationship(back_populates="matches_as_loser", foreign_keys=[loser_id])
    finder: Mapped["User"] = relationship(back_populates="matches_as_finder", foreign_keys=[finder_id])


