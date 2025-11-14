import enum
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum as SQLEnum, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base

if TYPE_CHECKING:
    from app.models.item import Item
    from app.models.match import Match


class UserRole(str, enum.Enum):
    USER = "USER"
    ADMIN = "ADMIN"


class User(Base):
    """Represents an authenticated user within the system."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(String(length=255), nullable=False)
    email: Mapped[str] = mapped_column(String(length=255), nullable=False, unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(length=255), nullable=False)
    roll_number: Mapped[str] = mapped_column(String(length=64), nullable=False, unique=True)
    hostel: Mapped[str | None] = mapped_column(String(length=128), nullable=True)
    contact_number: Mapped[str] = mapped_column(String(length=32), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        SQLEnum(UserRole, name="user_role"),
        nullable=False,
        default=UserRole.USER,
        server_default=UserRole.USER.value,
    )
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    reported_items: Mapped[list["Item"]] = relationship(
        back_populates="reported_by",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    matches_as_loser: Mapped[list["Match"]] = relationship(
        back_populates="loser",
        foreign_keys="Match.loser_id",
    )
    matches_as_finder: Mapped[list["Match"]] = relationship(
        back_populates="finder",
        foreign_keys="Match.finder_id",
    )

