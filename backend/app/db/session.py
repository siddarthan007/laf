from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncAttrs, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.sql import text

from app.config.settings import get_settings

settings = get_settings()


class Base(AsyncAttrs, DeclarativeBase):
    """Declarative base for ORM models."""


# Disable echo to prevent SQL query logging (too verbose)
# Set echo=False to suppress SQL query output
engine_args = {"echo": False, "pool_pre_ping": True}

# Always apply SSL mode from settings
engine_args["connect_args"] = {"sslmode": settings.database_ssl_mode}

print(f"Database connection args: echo={engine_args.get('echo')}, sslmode={engine_args['connect_args']['sslmode']}")

engine = create_async_engine(str(settings.database_url), **engine_args)
async_session_factory = async_sessionmaker(bind=engine, expire_on_commit=False)


async def get_session() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency that yields an async SQLAlchemy session."""

    async with async_session_factory() as session:
        yield session


async def ensure_database_extensions() -> None:
    """Enable required PostgreSQL extensions such as pgvector."""

    if not settings.pgvector_enabled:
        return

    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))


