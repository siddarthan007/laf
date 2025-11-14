import logging
import uuid
from pathlib import Path

import aiofiles
from fastapi import HTTPException, UploadFile, status

logger = logging.getLogger(__name__)


async def read_validated_upload(
    upload_file: UploadFile,
    *,
    allowed_mimetypes: tuple[str, ...],
    max_bytes: int,
) -> bytes:
    """Read an upload and enforce MIME type and size constraints."""

    if upload_file.content_type not in allowed_mimetypes:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file type '{upload_file.content_type}'. Allowed types: {', '.join(allowed_mimetypes)}",
        )

    data = await upload_file.read()
    if len(data) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum size of {max_bytes // (1024 * 1024)} MB",
        )

    return data


async def save_upload_file(
    upload_file: UploadFile,
    destination_dir: Path,
    *,
    file_bytes: bytes | None = None,
) -> Path:
    """Persist an uploaded file to the configured storage directory."""

    destination_dir.mkdir(parents=True, exist_ok=True)
    file_extension = Path(upload_file.filename or "").suffix or ".bin"
    file_name = f"{uuid.uuid4()}{file_extension}"
    target_path = destination_dir / file_name

    data = file_bytes if file_bytes is not None else await upload_file.read()

    async with aiofiles.open(target_path, "wb") as buffer:
        await buffer.write(data)

    await upload_file.close()
    return target_path


async def delete_upload_file(image_url: str | None, upload_dir: Path) -> None:
    """Delete an uploaded image file if it exists.
    
    Args:
        image_url: The image URL path (e.g., "/static/uploads/uuid.ext")
        upload_dir: The base upload directory path (e.g., "static/uploads")
    """
    if not image_url:
        return
    
    try:
        # Remove leading slash if present
        # image_url format: "/static/uploads/uuid.ext"
        # We need to extract just the filename: "uuid.ext"
        path_str = image_url.lstrip("/")
        path_parts = Path(path_str).parts
        
        # Extract filename from the path (last part)
        # path_parts could be: ("static", "uploads", "uuid.ext")
        filename = path_parts[-1] if path_parts else None
        
        if not filename:
            logger.warning(f"Could not extract filename from image URL: {image_url}")
            return
        
        # Construct the full file path
        file_path = upload_dir / filename
        
        # Ensure the file is within the upload directory for security
        upload_dir_abs = upload_dir.resolve()
        file_path_abs = file_path.resolve()
        
        # Security check: ensure file is within upload directory
        try:
            file_path_abs.relative_to(upload_dir_abs)
        except ValueError:
            logger.warning(f"Attempted to delete file outside upload directory: {image_url}")
            return
        
        # Delete the file if it exists
        if file_path_abs.exists() and file_path_abs.is_file():
            file_path_abs.unlink()
            logger.info(f"Deleted image file: {file_path_abs}")
        else:
            logger.debug(f"Image file not found (may have been already deleted): {file_path_abs}")
    except Exception as e:
        # Log error but don't fail the deletion operation
        logger.error(f"Failed to delete image file {image_url}: {e}", exc_info=True)

