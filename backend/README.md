# Lost & Found Backend

AI-powered university lost and found service built with FastAPI, PostgreSQL, and transformer embeddings. This backend exposes authentication, item reporting, and intelligent matching APIs according to the project specification.

## Environment configuration

Create an `.env` file in the project root (same directory as `pyproject.toml`) or set the variables directly in your deployment environment. All configuration keys live in `app/config/settings.py`. Common overrides:

```env
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/lostfound
JWT_SECRET_KEY=super-secret-change-me
SMTP_HOST=smtp.your-domain.com
SMTP_PORT=587
SMTP_USERNAME=lostfound
SMTP_PASSWORD=change-this
SMTP_USE_TLS=true
EMAIL_SENDER_ADDRESS=lostfound@your-domain.com
EMAIL_SENDER_NAME=University Lost & Found
ADMIN_OFFICE_NAME=Campus Admin Office
ADMIN_OFFICE_EMAIL=adminoffice@your-domain.com
ADMIN_OFFICE_CONTACT_NUMBER=+1-555-123-4567
UPLOAD_MAX_BYTES=5242880
UPLOAD_ALLOWED_MIMETYPES=["image/jpeg","image/png"]
```

## Database migrations

Alembic is pre-configured; run migrations with:

```bash
uv run alembic upgrade head
```

To generate new migrations:

```bash
uv run alembic revision --autogenerate -m "describe change"
uv run alembic upgrade head
```

Ensure the target database is reachable and the `vector` extension is available (the initial migration will create it when possible).

## Running locally

```bash
uv sync
uv run uvicorn app.main:app --reload
```


