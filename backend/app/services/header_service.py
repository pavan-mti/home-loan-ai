from __future__ import annotations

from pathlib import Path
from typing import Any
from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from ..models import HeaderTemplate
from ..repositories.header_repository import HeaderRepository
from .documents import STORAGE_ROOT
from .image_utils import save_header_image


class HeaderService:
    def __init__(self, repository: HeaderRepository):
        self.repository = repository

    def list_headers(self) -> list[HeaderTemplate]:
        return self.repository.get_all()

    def get_header(self, header_id: int) -> HeaderTemplate | None:
        return self.repository.get_by_id(header_id)

    def get_default_header(self) -> HeaderTemplate | None:
        return self.repository.get_default()

    async def create_header(
        self,
        *,
        header_name: str,
        file: UploadFile,
        display_order: int = 0,
        is_active: bool = True,
        is_default: bool = False,
    ) -> HeaderTemplate:
        image_path, width, height = await save_header_image(file)
        return self.repository.create(
            header_name=header_name,
            image_path=image_path,
            image_width=width,
            image_height=height,
            display_order=display_order,
            is_active=is_active,
            is_default=is_default,
        )

    async def update_header(
        self,
        header_id: int,
        *,
        header_name: str | None = None,
        file: UploadFile | None = None,
        display_order: int | None = None,
        is_active: bool | None = None,
        is_default: bool | None = None,
    ) -> HeaderTemplate:
        header = self.repository.get_by_id(header_id)
        if not header:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Header template not found"
            )

        update_data: dict[str, Any] = {}
        if header_name is not None:
            update_data["header_name"] = header_name
        if display_order is not None:
            update_data["display_order"] = display_order
        if is_active is not None:
            update_data["is_active"] = is_active
        if is_default is not None:
            update_data["is_default"] = is_default

        if file is not None:
            # Unlink old image file if it exists
            try:
                old_file_path = STORAGE_ROOT / "headers" / Path(header.image_path).name
                if old_file_path.exists() and old_file_path.is_file():
                    old_file_path.unlink()
            except Exception:
                pass

            new_image_path, width, height = await save_header_image(file)
            update_data["image_path"] = new_image_path
            update_data["image_width"] = width
            update_data["image_height"] = height

        return self.repository.update(header, **update_data)

    def set_default(self, header_id: int) -> HeaderTemplate:
        header = self.repository.get_by_id(header_id)
        if not header:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Header template not found"
            )
        return self.repository.update(header, is_default=True, is_active=True)

    def delete_header(self, header_id: int) -> dict[str, str]:
        header = self.repository.get_by_id(header_id)
        if not header:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Header template not found"
            )

        all_headers = self.repository.get_all()
        if header.is_default and len(all_headers) > 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete the default header. Please assign another header as default first."
            )

        try:
            file_path = STORAGE_ROOT / "headers" / Path(header.image_path).name
            if file_path.exists() and file_path.is_file():
                file_path.unlink()
        except Exception:
            pass

        self.repository.delete(header)
        return {"message": "Header template deleted successfully"}
