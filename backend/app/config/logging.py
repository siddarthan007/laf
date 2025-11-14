import logging
from typing import Any

import structlog


def configure_logging() -> None:
    """Configure application-wide structured logging using structlog."""

    timestamper = structlog.processors.TimeStamper(fmt="iso", utc=True)

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            timestamper,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.dev.ConsoleRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
    )
    
    # Suppress SQLAlchemy SQL query logging (too verbose)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.pool").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.dialects").setLevel(logging.WARNING)


def get_logger(*, name: str) -> structlog.stdlib.BoundLogger:
    """Return a pre-configured structlog logger."""

    return structlog.get_logger(name)


