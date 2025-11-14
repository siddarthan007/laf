import enum
import logging
import uuid
from pathlib import Path
from typing import TYPE_CHECKING

from pgvector.sqlalchemy import Vector
from sqlalchemy import Boolean, DateTime, Enum as SQLEnum, ForeignKey, String, Text, event, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.config.settings import get_settings
from app.db.session import Base

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from app.models.match import Match
    from app.models.user import User


class ItemStatus(str, enum.Enum):
    LOST = "LOST"
    FOUND = "FOUND"


class Item(Base):
    """Represents a lost or found item reported to the system."""

    __tablename__ = "items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    reported_by_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[ItemStatus] = mapped_column(
        SQLEnum(ItemStatus, name="item_status"),
        nullable=False,
        index=True,
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)
    location: Mapped[str] = mapped_column(String(length=255), nullable=False)
    image_url: Mapped[str | None] = mapped_column(String(length=512), nullable=True)

    description_vector: Mapped[list[float]] = mapped_column(Vector(384), nullable=False)
    description_clip_vector: Mapped[list[float]] = mapped_column(Vector(768), nullable=False)
    image_vector: Mapped[list[float] | None] = mapped_column(Vector(768), nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    is_admin_report: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    has_match_found: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    reported_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), index=True
    )

    reported_by: Mapped["User"] = relationship(back_populates="reported_items", lazy="joined")

    matches_as_lost: Mapped[list["Match"]] = relationship(
        back_populates="lost_item",
        foreign_keys="Match.lost_item_id",
        cascade="all, delete-orphan",
    )
    matches_as_found: Mapped[list["Match"]] = relationship(
        back_populates="found_item",
        foreign_keys="Match.found_item_id",
        cascade="all, delete-orphan",
    )


@event.listens_for(Item, "before_delete")
def delete_item_image(mapper, connection, target: Item):
    """Delete associated image file when an item is deleted (including cascade deletes)."""
    if target.image_url:
        try:
            settings = get_settings()
            
            # Remove leading slash if present
            path_str = target.image_url.lstrip("/")
            path_parts = Path(path_str).parts
            
            # Extract filename from the path (last part)
            filename = path_parts[-1] if path_parts else None
            
            if filename:
                file_path = settings.static_upload_dir / filename
                
                # Ensure the file is within the upload directory for security
                upload_dir_abs = settings.static_upload_dir.resolve()
                file_path_abs = file_path.resolve()
                
                # Security check: ensure file is within upload directory
                try:
                    file_path_abs.relative_to(upload_dir_abs)
                    # Delete the file if it exists
                    if file_path_abs.exists() and file_path_abs.is_file():
                        file_path_abs.unlink()
                        logger.info(f"Deleted image file via event handler: {file_path_abs}")
                except ValueError:
                    logger.warning(f"Attempted to delete file outside upload directory: {target.image_url}")
        except Exception as e:
            # Log error but don't fail the deletion operation
            logger.error(f"Failed to delete image file {target.image_url} via event handler: {e}", exc_info=True)


