from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class FreelancerCreate(BaseModel):
    username: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=6, max_length=255)
    confirm_password: str = Field(min_length=6, max_length=255)


class FreelancerLogin(BaseModel):
    username: str
    password: str


class FreelancerPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: int
    username: str
    created_date: datetime | None = None


class LoginResponse(BaseModel):
    token: str
    user: FreelancerPublic


class ValuerCreate(BaseModel):
    valuer_name: str = Field(min_length=1, max_length=255)
    valuer_contact: str = Field(min_length=1, max_length=100)
    valuer_header_image_path: str | None = None


class ValuerUpdate(BaseModel):
    valuer_name: str | None = Field(default=None, max_length=255)
    valuer_contact: str | None = Field(default=None, max_length=100)
    valuer_header_image_path: str | None = None


class HlcCreate(BaseModel):
    hlc_name: str = Field(min_length=1, max_length=255)
    hlc_contact: str = Field(min_length=1, max_length=100)
    hlc_area: str = Field(min_length=1, max_length=255)
    hlc_bank: str = Field(min_length=1, max_length=255)


class HlcUpdate(BaseModel):
    hlc_name: str | None = Field(default=None, max_length=255)
    hlc_contact: str | None = Field(default=None, max_length=100)
    hlc_area: str | None = Field(default=None, max_length=255)
    hlc_bank: str | None = Field(default=None, max_length=255)


class TemplateUpdate(BaseModel):
    template_key_id: str | None = Field(default=None, max_length=255)
    template_name: str | None = Field(default=None, max_length=255)
    template_bank: str | None = Field(default=None, max_length=255)
    template_content_json: dict[str, Any] | None = None
    original_docx_url: str | None = None


class TemplateFieldSpec(BaseModel):
    field_code: str
    label: str
    document_source: str | None = None
    keywords: list[str] = Field(default_factory=list)
    field_type: str = "text"
    static_value: str | None = None
    dynamic_value: str | None = None
    raw_text: str | None = None
    nested_fields: list["TemplateFieldSpec"] = Field(default_factory=list)


class TemplateTableSpec(BaseModel):
    name: str | None = None
    headers: list[str] = Field(default_factory=list)
    rows: list[list[str]] = Field(default_factory=list)


class TemplateSectionSpec(BaseModel):
    name: str
    fields: list[TemplateFieldSpec] = Field(default_factory=list)
    tables: list[TemplateTableSpec] = Field(default_factory=list)


class TemplateContentSpec(BaseModel):
    sections: list[TemplateSectionSpec] = Field(default_factory=list)


TemplateFieldSpec.model_rebuild()
TemplateSectionSpec.model_rebuild()


class TemplateCreate(BaseModel):
    template_key_id: str = Field(min_length=1, max_length=255)
    template_name: str = Field(min_length=1, max_length=255)
    template_bank: str = Field(min_length=1, max_length=255)
    template_content_json: TemplateContentSpec
    original_docx_url: str | None = None


class TemplateImportResponse(BaseModel):
    template_id: int
    template_key_id: str
    template_name: str
    template_bank: str
    template_content_json: TemplateContentSpec
    original_docx_url: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class TemplateListItem(BaseModel):
    template_id: int
    template_key_id: str
    template_name: str
    template_bank: str
    original_docx_url: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class ExtractionResponse(BaseModel):
    applicant_name: str | None = None
    survey_number: str | None = None
    plot_number: str | None = None
    permission_number: str | None = None
    property_address: str | None = None
    built_up_area: str | None = None
    land_area: str | None = None
    document_number: str | None = None
    registration_details: str | None = None
    confidence: float | None = None


class PermissionUploadResponse(BaseModel):
    document_id: int
    permission_number: str | None = None
    extracted_text: str
    analysis: dict[str, Any]