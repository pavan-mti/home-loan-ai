from __future__ import annotations

import uuid
from pathlib import Path
from fastapi import HTTPException, UploadFile, status
from PIL import Image

from .documents import STORAGE_ROOT

ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg"}
MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024  # 5MB


async def validate_image(file: UploadFile) -> str:
    suffix = Path(file.filename or "header.png").suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only JPG, JPEG, and PNG files are allowed"
        )
    content = await file.read()
    if len(content) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size must be less than 5MB"
        )
    await file.seek(0)
    return suffix


def extract_dimensions_from_path(file_path: Path) -> tuple[int | None, int | None]:
    try:
        with Image.open(file_path) as img:
            return img.width, img.height
    except Exception:
        return None, None


async def save_header_image(file: UploadFile) -> tuple[str, int | None, int | None]:
    suffix = await validate_image(file)
    headers_dir = STORAGE_ROOT / "headers"
    headers_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{uuid.uuid4().hex}{suffix}"
    saved_path = headers_dir / filename

    with saved_path.open("wb") as buffer:
        import shutil
        shutil.copyfileobj(file.file, buffer)

    width, height = extract_dimensions_from_path(saved_path)
    image_path = f"/storage/headers/{filename}"
    return image_path, width, height
