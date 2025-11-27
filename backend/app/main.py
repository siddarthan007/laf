from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config.logging import configure_logging
from app.config.settings import get_settings
from app.db.session import ensure_database_extensions
from app.routers import api_router
from app.services.embeddings import embedding_service

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    await ensure_database_extensions()
    await embedding_service.load()
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.project_name,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.backend_cors_origins] + [
            "https://staging.d1mkzua6r0j55a.amplifyapp.com",
            "http://localhost:5173",
            "http://localhost:3000",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router)


    
    base_dir = Path(__file__).resolve().parent.parent
    static_dir = base_dir / "static"
    
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    @app.get("/health", tags=["system"])
    async def health_check() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()

try:
    from mangum import Mangum
    handler = Mangum(app, lifespan="on")
except ImportError:
    handler = None


