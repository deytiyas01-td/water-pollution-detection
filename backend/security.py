import uuid
from pathlib import Path
from fastapi import HTTPException, Security, Request, status
from fastapi.security.api_key import APIKeyHeader
from backend.config import (
    API_SECRET_KEY,
    ALLOWED_IMAGE_EXTENSIONS,
    ALLOWED_VIDEO_EXTENSIONS,
    MAX_IMAGE_SIZE_MB,
    MAX_VIDEO_SIZE_MB,
)

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(api_key: str = Security(api_key_header)):
    """
    Enforces API key security if API_SECRET_KEY is defined in .env.
    Keeps API keys private and prevents unauthorized calls.
    """
    if API_SECRET_KEY:
        if not api_key or api_key.strip() != API_SECRET_KEY:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid or missing API Key. Set X-API-Key header.",
            )
    return api_key


def sanitize_filename(filename: str) -> str:
    """
    Generates a secure random filename preserving the valid extension to prevent path traversal.
    """
    ext = Path(filename).suffix.lower()
    return f"{uuid.uuid4().hex}{ext}"


def validate_file_extension(filename: str, expected_type: str = "any") -> tuple[str, str]:
    """
    Validates file extension against allowed image/video formats.
    Returns (media_type, extension).
    """
    ext = Path(filename).suffix.lower()

    is_image = ext in ALLOWED_IMAGE_EXTENSIONS
    is_video = ext in ALLOWED_VIDEO_EXTENSIONS

    if not is_image and not is_video:
        allowed = list(ALLOWED_IMAGE_EXTENSIONS | ALLOWED_VIDEO_EXTENSIONS)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format '{ext}'. Allowed: {', '.join(allowed)}",
        )

    if expected_type == "image" and not is_image:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Expected an image ({', '.join(ALLOWED_IMAGE_EXTENSIONS)}), got '{ext}'",
        )

    if expected_type == "video" and not is_video:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Expected a video ({', '.join(ALLOWED_VIDEO_EXTENSIONS)}), got '{ext}'",
        )

    media_type = "image" if is_image else "video"
    return media_type, ext


def validate_file_size(size_bytes: int, media_type: str):
    """
    Validates file size against configured maximum limits.
    """
    if media_type == "image":
        max_bytes = MAX_IMAGE_SIZE_MB * 1024 * 1024
        if size_bytes > max_bytes:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Image size exceeds limit of {MAX_IMAGE_SIZE_MB}MB.",
            )
    elif media_type == "video":
        max_bytes = MAX_VIDEO_SIZE_MB * 1024 * 1024
        if size_bytes > max_bytes:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Video size exceeds limit of {MAX_VIDEO_SIZE_MB}MB.",
            )
