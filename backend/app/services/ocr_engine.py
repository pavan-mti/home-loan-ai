from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import UploadFile

from .documents import extract_text_from_upload, save_upload


class OCREngine:
    def extract_from_file(self, file_path: Path) -> str:
        return extract_text_from_upload(file_path)

    def extract_from_upload(self, upload: UploadFile, subfolder: str = "documents") -> tuple[Path, str]:
        saved_path = save_upload(upload, subfolder)
        return saved_path, extract_text_from_upload(saved_path)

    def extract_bundle(self, uploads: list[UploadFile]) -> dict[str, dict[str, Any]]:
        bundle: dict[str, dict[str, Any]] = {}
        for upload in uploads:
            saved_path, extracted_text = self.extract_from_upload(upload)
            source_name = Path(upload.filename or saved_path.name).stem.upper()
            bundle[source_name] = {
                "file_name": upload.filename or saved_path.name,
                "file_path": str(saved_path),
                "text": extracted_text,
            }
        return bundle