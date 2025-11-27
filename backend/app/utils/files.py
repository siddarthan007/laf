import logging
import uuid
import asyncio
from pathlib import Path
from typing import Optional

import aiofiles
import boto3
from botocore.exceptions import ClientError
from fastapi import HTTPException, UploadFile, status

from app.config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


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
) -> str:
    """
    Persist an uploaded file.
    
    If S3_BUCKET_NAME is set, uploads to S3 and returns the public URL.
    Otherwise, saves to the local filesystem and returns the relative path.
    """
    file_extension = Path(upload_file.filename or "").suffix or ".bin"
    file_name = f"{uuid.uuid4()}{file_extension}"
    data = file_bytes if file_bytes is not None else await upload_file.read()

    # S3 Upload
    if settings.s3_bucket_name:
        try:
            s3_client = boto3.client("s3", region_name=settings.aws_region)
            
            # Run blocking S3 call in a thread
            await asyncio.to_thread(
                s3_client.put_object,
                Bucket=settings.s3_bucket_name,
                Key=file_name,
                Body=data,
                ContentType=upload_file.content_type or "application/octet-stream",
            )
            
            # Return the public URL
            # If using CloudFront, this should ideally be the CloudFront URL, 
            # but standard S3 URL is a safe default for now.
            return f"https://{settings.s3_bucket_name}.s3.{settings.aws_region}.amazonaws.com/{file_name}"
            
        except Exception as e:
            logger.error(f"Failed to upload to S3: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Failed to upload file to storage")
            
    # Local Upload (Fallback)
    destination_dir.mkdir(parents=True, exist_ok=True)
    target_path = destination_dir / file_name

    async with aiofiles.open(target_path, "wb") as buffer:
        await buffer.write(data)

    await upload_file.close()
    
    # Return relative path for local storage (e.g., "/static/uploads/uuid.ext")
    # We prepend a slash so the frontend treats it as an absolute path from root
    return f"/static/uploads/{file_name}"


async def delete_upload_file(image_url: str | None, upload_dir: Path) -> None:
    """Delete an uploaded image file from S3 or local disk."""
    if not image_url:
        return
    
    # Check if it's an S3 URL
    if image_url.startswith("http") and settings.s3_bucket_name:
        try:
            # Extract key from URL
            # URL: https://bucket.s3.region.amazonaws.com/filename.ext
            filename = image_url.split("/")[-1]
            
            s3_client = boto3.client("s3", region_name=settings.aws_region)
            await asyncio.to_thread(
                s3_client.delete_object,
                Bucket=settings.s3_bucket_name,
                Key=filename
            )
            logger.info(f"Deleted S3 object: {filename}")
            return
        except Exception as e:
            logger.error(f"Failed to delete from S3: {e}", exc_info=True)
            return

    # Local Deletion
    try:
        # Remove leading slash if present
        path_str = image_url.lstrip("/")
        path_parts = Path(path_str).parts
        filename = path_parts[-1] if path_parts else None
        
        if not filename:
            return
        
        file_path = upload_dir / filename
        if file_path.exists():
            file_path.unlink()
            logger.info(f"Deleted local file: {file_path}")
            
    except Exception as e:
        logger.error(f"Failed to delete local file: {e}", exc_info=True)
