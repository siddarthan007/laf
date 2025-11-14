from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

import bcrypt
from jose import JWTError, jwt

from app.config.settings import get_settings
from app.schemas.auth import TokenPayload

settings = get_settings()

# Bcrypt configuration
BCRYPT_ROUNDS = 12


def hash_password(plain_password: str) -> str:
    """Hash and salt a plain user password using bcrypt directly."""
    # Bcrypt has a 72-byte limit, so we need to ensure the password doesn't exceed this
    password_bytes = plain_password.encode('utf-8')
    if len(password_bytes) > 72:
        password_bytes = password_bytes[:72]
    
    # Generate salt and hash password
    salt = bcrypt.gensalt(rounds=BCRYPT_ROUNDS)
    hashed = bcrypt.hashpw(password_bytes, salt)
    
    # Return as string (bcrypt returns bytes)
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a candidate password against the stored hash using bcrypt directly."""
    # Bcrypt has a 72-byte limit, so we need to ensure the password doesn't exceed this
    password_bytes = plain_password.encode('utf-8')
    if len(password_bytes) > 72:
        password_bytes = password_bytes[:72]
    
    # Convert hashed password back to bytes and verify
    hashed_bytes = hashed_password.encode('utf-8')
    
    try:
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    except (ValueError, TypeError):
        return False


def _build_token(*, subject: UUID, expires_delta: timedelta) -> str:
    expire_at = datetime.now(timezone.utc) + expires_delta
    to_encode: dict[str, Any] = {"sub": str(subject), "exp": expire_at}
    encoded_jwt = jwt.encode(
        to_encode,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )
    return encoded_jwt


def create_access_token(*, subject: UUID) -> str:
    """Generate a JWT access token for the given subject."""

    return _build_token(
        subject=subject,
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
    )


def create_refresh_token(*, subject: UUID) -> str:
    """Generate a JWT refresh token for the given subject."""

    return _build_token(
        subject=subject,
        expires_delta=timedelta(minutes=settings.refresh_token_expire_minutes),
    )


def decode_token(token: str) -> TokenPayload:
    """Decode a JWT token and return the payload."""

    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except JWTError as exc:
        raise ValueError("Invalid token") from exc

    if "sub" not in payload or "exp" not in payload:
        raise ValueError("Missing token claims")

    try:
        subject = UUID(payload["sub"])
    except (ValueError, TypeError) as exc:
        raise ValueError("Malformed subject claim") from exc

    expires_at = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
    return TokenPayload(sub=subject, exp=expires_at)

