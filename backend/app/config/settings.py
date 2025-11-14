from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    project_name: str = "Lost & Found API"
    environment: str = Field(default="development", validation_alias="ENVIRONMENT")

    database_url: str = Field(
        default="postgresql+psycopg://postgres:postgres@localhost:5432/lostfound",
        alias="DATABASE_URL",
    )
    pgvector_enabled: bool = Field(default=True, alias="PGVECTOR_ENABLED")

    jwt_secret_key: str = Field(default="change-this-secret", alias="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(default=60, alias="JWT_ACCESS_EXP_MINUTES")
    refresh_token_expire_minutes: int = Field(default=60 * 24 * 7, alias="JWT_REFRESH_EXP_MINUTES")

    clip_model_name: str = Field(default="sentence-transformers/clip-ViT-L-14", alias="CLIP_MODEL_NAME")
    text_embedding_model_name: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2", alias="TEXT_EMBEDDING_MODEL_NAME"
    )
    embeddings_device: str = Field(default="cpu", alias="EMBEDDINGS_DEVICE")
    embeddings_batch_size: int = Field(default=8, alias="EMBEDDINGS_BATCH_SIZE")

    static_upload_dir: Path = Field(default=Path("static/uploads"), alias="STATIC_UPLOAD_DIR")
    match_confidence_threshold: float = Field(default=0.70, alias="MATCH_CONFIDENCE_THRESHOLD")
    max_matches_returned: int = Field(default=20, alias="MAX_MATCHES_RETURNED")
    upload_max_bytes: int = Field(default=5 * 1024 * 1024, alias="UPLOAD_MAX_BYTES")
    upload_allowed_mimetypes: tuple[str, ...] = Field(
        default=("image/jpeg", "image/png", "image/webp"), alias="UPLOAD_ALLOWED_MIMETYPES"
    )

    email_sender_address: str = Field(default="noreply@lostfound.local", alias="EMAIL_SENDER_ADDRESS")
    admin_office_name: str = Field(default="Campus Admin Office", alias="ADMIN_OFFICE_NAME")
    admin_office_email: str = Field(default="admin-office@university.local", alias="ADMIN_OFFICE_EMAIL")
    admin_office_contact_number: str = Field(default="000-000-0000", alias="ADMIN_OFFICE_CONTACT_NUMBER")
    email_sender_name: str = Field(default="Lost & Found Desk", alias="EMAIL_SENDER_NAME")
    smtp_host: str = Field(default="localhost", alias="SMTP_HOST")
    smtp_port: int = Field(default=1025, alias="SMTP_PORT")
    smtp_username: str | None = Field(default=None, alias="SMTP_USERNAME")
    smtp_password: str | None = Field(default=None, alias="SMTP_PASSWORD")
    smtp_use_tls: bool = Field(default=False, alias="SMTP_USE_TLS")
    smtp_timeout_seconds: int = Field(default=30, alias="SMTP_TIMEOUT_SECONDS")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached application settings instance."""

    settings = Settings()
    settings.static_upload_dir.mkdir(parents=True, exist_ok=True)
    return settings

