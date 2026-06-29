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
    id: int
    template_id: int
    template_key_id: str
    template_name: str
    template_bank: str
    template_content_json: TemplateContentSpec
    original_docx_url: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class TemplateListItem(BaseModel):
    id: int
    template_id: int
    template_key_id: str
    template_name: str
    template_bank: str
    field_count: int = 0
    original_docx_url: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class ScoredField(BaseModel):
    value: str | None = None
    source_page: int | None = None
    ocr_confidence: float = 0.0
    regex_confidence: float = 0.0
    final_confidence: float = 0.0
    validation_status: str | None = "valid"
    validation_message: str | None = None


class ExtractionResponse(BaseModel):
    inspection_date: ScoredField | None = None
    valuation_date: ScoredField | None = None
    owner_name: ScoredField | None = None
    purchaser_details: ScoredField | None = None
    property_description: ScoredField | None = None
    prohibited_property_details: ScoredField | None = None
    legal_opinion: ScoredField | None = None
    mortgage_details: ScoredField | None = None
    ftl_buffer_zone_details: ScoredField | None = None
    plot_survey_number: ScoredField | None = None
    door_house_number: ScoredField | None = None
    ts_number_village: ScoredField | None = None
    ward_taluka: ScoredField | None = None
    mandal_district: ScoredField | None = None
    property_address: ScoredField | None = None
    confidence: float | None = None


class PermissionUploadResponse(BaseModel):
    document_id: int
    permission_number: str | None = None
    extracted_text: str
    analysis: list[dict[str, Any]]
    required_fields: list[str]



class TemplateFieldResponse(BaseModel):
    id: int
    field_name: str
    display_order: int
    field_type: str = "dynamic"
    static_value: str | None = None

    model_config = ConfigDict(from_attributes=True)


class TemplateFieldsGetResponse(BaseModel):
    template_id: int
    template_name: str
    fields: list[TemplateFieldResponse]

    model_config = ConfigDict(from_attributes=True)


class TemplateUploadResponse(BaseModel):
    template_id: int
    template_name: str
    field_count: int
    fields: list[str]


class TemplateDetailResponse(BaseModel):
    id: int
    name: str
    field_count: int
    fields: list[TemplateFieldResponse]


class HeaderTemplateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    header_name: str
    image_path: str
    image_width: int | None = None
    image_height: int | None = None
    display_order: int = 0
    is_active: bool
    is_default: bool = False
    created_at: datetime | None = None
    updated_at: datetime | None = None


class RenderingOptions(BaseModel):
    header_id: int | None = None
    certificate_enabled: bool = True


class GenerateReportRequest(BaseModel):
    field_values: dict[str, Any] = Field(default_factory=dict)
    rendering_options: RenderingOptions = Field(default_factory=RenderingOptions)



class CompletionCertificateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    template_text: str
    created_at: datetime | None = None
    updated_at: datetime | None = None


class CompletionCertificateUpdate(BaseModel):
    template_text: str


class MapSavedFieldsRequest(BaseModel):
    document_id: int