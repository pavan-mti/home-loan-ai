from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


JSON_TYPE = JSON().with_variant(JSONB(), "postgresql")


class TimestampMixin:
    created_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class Freelancer(Base, TimestampMixin):
    __tablename__ = "freelancers"

    user_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    def to_dict(self) -> dict[str, Any]:
        return {
            "user_id": self.user_id,
            "username": self.username,
            "created_date": self.created_date.isoformat() if self.created_date else None,
        }


class SessionToken(Base):
    __tablename__ = "session_tokens"

    token_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("freelancers.user_id"), nullable=False, index=True)
    token: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    created_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class Valuer(Base, TimestampMixin):
    __tablename__ = "valuers"

    valuer_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    valuer_name: Mapped[str] = mapped_column(String(255), nullable=False)
    valuer_contact: Mapped[str] = mapped_column(String(100), nullable=False)
    valuer_header_image_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_by_user_id: Mapped[int] = mapped_column(ForeignKey("freelancers.user_id"), nullable=False, index=True)

    def to_dict(self) -> dict[str, Any]:
        return {
            "valuer_id": self.valuer_id,
            "valuer_name": self.valuer_name,
            "valuer_contact": self.valuer_contact,
            "valuer_header_image_path": self.valuer_header_image_path,
            "created_by_user_id": self.created_by_user_id,
            "created_date": self.created_date.isoformat() if self.created_date else None,
        }


class Hlc(Base, TimestampMixin):
    __tablename__ = "hlc"

    hlc_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    hlc_name: Mapped[str] = mapped_column(String(255), nullable=False)
    hlc_contact: Mapped[str] = mapped_column(String(100), nullable=False)
    hlc_area: Mapped[str] = mapped_column(String(255), nullable=False)
    hlc_bank: Mapped[str] = mapped_column(String(255), nullable=False)
    created_by_user_id: Mapped[int] = mapped_column(ForeignKey("freelancers.user_id"), nullable=False, index=True)

    def to_dict(self) -> dict[str, Any]:
        return {
            "hlc_id": self.hlc_id,
            "hlc_name": self.hlc_name,
            "hlc_contact": self.hlc_contact,
            "hlc_area": self.hlc_area,
            "hlc_bank": self.hlc_bank,
            "created_by_user_id": self.created_by_user_id,
            "created_date": self.created_date.isoformat() if self.created_date else None,
        }


class Template(Base, TimestampMixin):
    __tablename__ = "templates"

    template_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    template_key_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    template_name: Mapped[str] = mapped_column(String(255), nullable=False)
    template_bank: Mapped[str] = mapped_column(String(255), nullable=False)
    template_content_json: Mapped[dict[str, Any]] = mapped_column(JSON_TYPE, nullable=False, default=dict)
    original_docx_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def to_dict(self) -> dict[str, Any]:
        return {
            "template_id": self.template_id,
            "template_key_id": self.template_key_id,
            "template_name": self.template_name,
            "template_bank": self.template_bank,
            "template_content_json": self.template_content_json,
            "original_docx_url": self.original_docx_url,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class PermissionDocument(Base, TimestampMixin):
    __tablename__ = "permission_documents"

    document_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    extracted_text: Mapped[str] = mapped_column(Text, nullable=False)
    permission_number: Mapped[str | None] = mapped_column(String(255), nullable=True)
    extracted_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    created_by_user_id: Mapped[int] = mapped_column(ForeignKey("freelancers.user_id"), nullable=False, index=True)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    audit_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("freelancers.user_id"), nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    entity: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    details_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    created_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)