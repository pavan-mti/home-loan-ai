from __future__ import annotations

import json
from datetime import datetime, timedelta
from typing import Any

from fastapi import Depends, FastAPI, File, Header, Form, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from .database import Base, engine, get_db
from .dependencies import get_template_service
from .models import AuditLog, Freelancer, Hlc, PermissionDocument, SessionToken, Valuer
from .schemas import (
    ExtractionResponse,
    FreelancerCreate,
    FreelancerLogin,
    FreelancerPublic,
    HlcCreate,
    HlcUpdate,
    LoginResponse,
    PermissionUploadResponse,
    TemplateCreate,
    TemplateImportResponse,
    TemplateListItem,
    TemplateUpdate,
    ValuerCreate,
    ValuerUpdate,
)
from .security import create_token, hash_password, verify_password
from .services.documents import STORAGE_ROOT, analyze_document, extract_permission_number, extract_text_from_upload, save_upload
from .services.template_service import TemplateService

app = FastAPI(title="Home Loan Valuation AI", version="0.1.0")

STORAGE_ROOT.mkdir(parents=True, exist_ok=True)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/storage", StaticFiles(directory=STORAGE_ROOT), name="storage")


def _ensure_database() -> None:
    Base.metadata.create_all(bind=engine)


@app.on_event("startup")
def on_startup() -> None:
    STORAGE_ROOT.mkdir(parents=True, exist_ok=True)
    _ensure_database()


def _audit(db: Session, user_id: int | None, action: str, entity: str, entity_id: str | None, details: dict[str, Any] | None = None) -> None:
    db.add(
        AuditLog(
            user_id=user_id,
            action=action,
            entity=entity,
            entity_id=entity_id,
            details_json=details or {},
        )
    )


def _get_bearer_token(authorization: str = Header(default="")) -> str:
    prefix = "Bearer "
    if not authorization.startswith(prefix):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    return authorization.removeprefix(prefix).strip()


def get_current_user(db: Session = Depends(get_db), token_value: str = Depends(_get_bearer_token)) -> Freelancer:
    token = (
        db.query(SessionToken)
        .filter(SessionToken.token == token_value, SessionToken.revoked_at.is_(None))
        .first()
    )
    if token is None or token.expires_at < datetime.utcnow():
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired or invalid")

    user = db.get(Freelancer, token.user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


@app.get("/")
def home() -> dict[str, str]:
    return {"message": "Home Loan Valuation AI Running"}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/auth/register", response_model=FreelancerPublic, status_code=status.HTTP_201_CREATED)
def register_freelancer(payload: FreelancerCreate, db: Session = Depends(get_db)) -> Freelancer:
    existing_user = db.query(Freelancer).filter(Freelancer.username == payload.username).first()
    if existing_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already exists")

    if payload.password != payload.confirm_password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Passwords do not match")

    freelancer = Freelancer(username=payload.username, password_hash=hash_password(payload.password))
    db.add(freelancer)
    db.flush()
    _audit(db, freelancer.user_id, "register", "freelancer", str(freelancer.user_id), {"username": freelancer.username})
    db.commit()
    db.refresh(freelancer)
    return freelancer


@app.post("/auth/login", response_model=LoginResponse)
def login_freelancer(payload: FreelancerLogin, db: Session = Depends(get_db)) -> LoginResponse:
    user = db.query(Freelancer).filter(Freelancer.username == payload.username).first()
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")

    token_value = create_token()
    db.add(SessionToken(user_id=user.user_id, token=token_value, expires_at=datetime.utcnow() + timedelta(days=30)))
    _audit(db, user.user_id, "login", "freelancer", str(user.user_id), {"username": user.username})
    db.commit()
    return LoginResponse(token=token_value, user=FreelancerPublic.model_validate(user))


@app.get("/auth/me", response_model=FreelancerPublic)
def get_me(current_user: Freelancer = Depends(get_current_user)) -> Freelancer:
    return current_user


@app.post("/auth/logout")
def logout(
    db: Session = Depends(get_db),
    token_value: str = Depends(_get_bearer_token),
    current_user: Freelancer = Depends(get_current_user),
) -> dict[str, str]:
    token = db.query(SessionToken).filter(SessionToken.token == token_value, SessionToken.revoked_at.is_(None)).first()
    if token is not None:
        token.revoked_at = datetime.utcnow()
        _audit(db, current_user.user_id, "logout", "freelancer", str(current_user.user_id), None)
        db.commit()
    return {"message": "Logged out"}


@app.get("/dashboard")
def dashboard(current_user: Freelancer = Depends(get_current_user)) -> dict[str, Any]:
    return {
        "user": FreelancerPublic.model_validate(current_user),
        "links": {
            "ghmc_public_search": "https://dpms.ghmc.telangana.gov.in/AutoDCR.Common2/CitizenSearch/publicsearch.aspx?sName=GHMC&edFlag=0&iVal=1",
            "telangana_buildnow": "https://app.buildnow.telangana.gov.in/login",
        },
    }


@app.post("/valuers", status_code=status.HTTP_201_CREATED)
def create_valuer(
    payload: ValuerCreate,
    db: Session = Depends(get_db),
    current_user: Freelancer = Depends(get_current_user),
) -> dict[str, Any]:
    valuer = Valuer(
        valuer_name=payload.valuer_name,
        valuer_contact=payload.valuer_contact,
        valuer_header_image_path=payload.valuer_header_image_path,
        created_by_user_id=current_user.user_id,
    )
    db.add(valuer)
    db.flush()
    _audit(db, current_user.user_id, "create", "valuer", str(valuer.valuer_id), payload.model_dump())
    db.commit()
    db.refresh(valuer)
    return valuer.to_dict()


@app.get("/valuers")
def list_valuers(db: Session = Depends(get_db), current_user: Freelancer = Depends(get_current_user)) -> list[dict[str, Any]]:
    valuers = db.query(Valuer).filter(Valuer.created_by_user_id == current_user.user_id).order_by(Valuer.created_date.desc()).all()
    return [valuer.to_dict() for valuer in valuers]


@app.put("/valuers/{valuer_id}")
def update_valuer(
    valuer_id: int,
    payload: ValuerUpdate,
    db: Session = Depends(get_db),
    current_user: Freelancer = Depends(get_current_user),
) -> dict[str, Any]:
    valuer = db.get(Valuer, valuer_id)
    if valuer is None or valuer.created_by_user_id != current_user.user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Valuer not found")

    if payload.valuer_name is not None:
        valuer.valuer_name = payload.valuer_name
    if payload.valuer_contact is not None:
        valuer.valuer_contact = payload.valuer_contact
    if payload.valuer_header_image_path is not None:
        valuer.valuer_header_image_path = payload.valuer_header_image_path
    _audit(db, current_user.user_id, "update", "valuer", str(valuer.valuer_id), payload.model_dump(exclude_none=True))
    db.commit()
    db.refresh(valuer)
    return valuer.to_dict()


@app.delete("/valuers/{valuer_id}")
def delete_valuer(
    valuer_id: int,
    db: Session = Depends(get_db),
    current_user: Freelancer = Depends(get_current_user),
) -> dict[str, str]:
    valuer = db.get(Valuer, valuer_id)
    if valuer is None or valuer.created_by_user_id != current_user.user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Valuer not found")
    db.delete(valuer)
    _audit(db, current_user.user_id, "delete", "valuer", str(valuer_id), None)
    db.commit()
    return {"message": "Valuer deleted"}


@app.post("/hlc", status_code=status.HTTP_201_CREATED)
def create_hlc(
    payload: HlcCreate,
    db: Session = Depends(get_db),
    current_user: Freelancer = Depends(get_current_user),
) -> dict[str, Any]:
    hlc = Hlc(
        hlc_name=payload.hlc_name,
        hlc_contact=payload.hlc_contact,
        hlc_area=payload.hlc_area,
        hlc_bank=payload.hlc_bank,
        created_by_user_id=current_user.user_id,
    )
    db.add(hlc)
    db.flush()
    _audit(db, current_user.user_id, "create", "hlc", str(hlc.hlc_id), payload.model_dump())
    db.commit()
    db.refresh(hlc)
    return hlc.to_dict()


@app.get("/hlc")
def list_hlc(db: Session = Depends(get_db), current_user: Freelancer = Depends(get_current_user)) -> list[dict[str, Any]]:
    hlc_records = db.query(Hlc).filter(Hlc.created_by_user_id == current_user.user_id).order_by(Hlc.created_date.desc()).all()
    return [record.to_dict() for record in hlc_records]


@app.put("/hlc/{hlc_id}")
def update_hlc(
    hlc_id: int,
    payload: HlcUpdate,
    db: Session = Depends(get_db),
    current_user: Freelancer = Depends(get_current_user),
) -> dict[str, Any]:
    record = db.get(Hlc, hlc_id)
    if record is None or record.created_by_user_id != current_user.user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="HLC not found")

    for field_name, value in payload.model_dump(exclude_none=True).items():
        setattr(record, field_name, value)
    _audit(db, current_user.user_id, "update", "hlc", str(record.hlc_id), payload.model_dump(exclude_none=True))
    db.commit()
    db.refresh(record)
    return record.to_dict()


@app.delete("/hlc/{hlc_id}")
def delete_hlc(
    hlc_id: int,
    db: Session = Depends(get_db),
    current_user: Freelancer = Depends(get_current_user),
) -> dict[str, str]:
    record = db.get(Hlc, hlc_id)
    if record is None or record.created_by_user_id != current_user.user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="HLC not found")
    db.delete(record)
    _audit(db, current_user.user_id, "delete", "hlc", str(hlc_id), None)
    db.commit()
    return {"message": "HLC deleted"}


@app.post("/templates", response_model=TemplateImportResponse, status_code=status.HTTP_201_CREATED)
def create_template(payload: TemplateCreate, template_service: TemplateService = Depends(get_template_service)) -> dict[str, Any]:
    return template_service.create_template(payload)


@app.post("/templates/import-docx", response_model=TemplateImportResponse, status_code=status.HTTP_201_CREATED)
async def import_template_docx(
    template_key_id: str = Form(...),
    template_name: str = Form(...),
    template_bank: str = Form(...),
    file: UploadFile = File(...),
    template_service: TemplateService = Depends(get_template_service),
) -> dict[str, Any]:
    return template_service.import_docx(
        template_key_id=template_key_id,
        template_name=template_name,
        template_bank=template_bank,
        upload=file,
    )


@app.post("/templates/import", response_model=TemplateImportResponse, status_code=status.HTTP_201_CREATED)
async def import_template(
    template_key_id: str = Form(...),
    template_name: str = Form(...),
    template_bank: str = Form(...),
    file: UploadFile = File(...),
    template_service: TemplateService = Depends(get_template_service),
) -> dict[str, Any]:
    return template_service.import_template(
        template_key_id=template_key_id,
        template_name=template_name,
        template_bank=template_bank,
        upload=file,
    )


@app.get("/templates", response_model=list[TemplateListItem])
def list_templates(template_service: TemplateService = Depends(get_template_service)) -> list[dict[str, Any]]:
    return template_service.list_templates()


@app.get("/templates/{template_id}", response_model=TemplateImportResponse)
def get_template(template_id: int, template_service: TemplateService = Depends(get_template_service)) -> dict[str, Any]:
    template = template_service.get_template(template_id)
    if template is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")
    return template


@app.put("/templates/{template_id}", response_model=TemplateImportResponse)
def update_template(template_id: int, payload: TemplateUpdate, template_service: TemplateService = Depends(get_template_service)) -> dict[str, Any]:
    updated = template_service.update_template(template_id, payload)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")
    return updated


@app.delete("/templates/{template_id}")
def delete_template(template_id: int, template_service: TemplateService = Depends(get_template_service)) -> dict[str, str]:
    deleted = template_service.delete_template(template_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")
    return {"message": "Template deleted"}


@app.post("/templates/{template_id}/map-fields")
def map_template_fields(
    template_id: int,
    uploads: list[UploadFile] = File(...),
    template_service: TemplateService = Depends(get_template_service),
) -> dict[str, Any]:
    saved_paths = []
    for upload in uploads:
        saved_paths.append(save_upload(upload, "documents"))
    return template_service.map_fields(template_id, saved_paths)


@app.post("/templates/{template_id}/generate-report")
def generate_report(template_id: int, field_values: dict[str, Any], template_service: TemplateService = Depends(get_template_service)) -> dict[str, Any]:
    output_path = template_service.generate_report(template_id, field_values)
    return {"report_url": f"/storage/reports/{output_path.name}", "file_path": str(output_path)}


@app.post("/reports/generate/{template_id}")
async def generate_report_endpoint(
    template_id: int,
    files: list[UploadFile] = File(...),
    template_service: TemplateService = Depends(get_template_service),
) -> FileResponse:
    template = template_service.repository.get_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    if not template.original_docx_url:
        raise HTTPException(status_code=400, detail="Template document file not found")

    saved_paths = []
    for upload in files:
        saved_paths.append(save_upload(upload, "documents"))

    mapped_data = template_service.map_fields(template_id, saved_paths)
    
    field_values = {}
    import re
    
    def walk_fields(fields_list):
        for f in fields_list:
            val = f.get("extracted_value")
            conf = f.get("confidence", 0.0)
            nr = f.get("needs_review", False)
            if val is not None and val != "":
                payload = {"value": val, "confidence": conf, "needs_review": nr}
                if f.get("field_code"):
                    field_values[f["field_code"]] = payload
                if f.get("label"):
                    field_values[f["label"]] = payload
                    slug = re.sub(r"[^a-z0-9]+", "_", f["label"].lower()).strip("_")
                    if slug:
                        field_values[slug] = payload
            nested = f.get("nested_fields")
            if nested:
                walk_fields(nested)
                
    for section in mapped_data.get("sections", []):
        walk_fields(section.get("fields", []))

    import uuid
    output_name = f"report_{uuid.uuid4().hex}.docx"
    generated_file = template_service.generate_report(template_id, field_values, output_name=output_name)

    return FileResponse(
        path=str(generated_file),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename="valuation_report.docx"
    )


@app.post("/documents/permission-number", response_model=PermissionUploadResponse)
async def get_permission_number(
    upload: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: Freelancer = Depends(get_current_user),
) -> PermissionUploadResponse:
    saved_path = save_upload(upload, "documents")
    extracted_text = extract_text_from_upload(saved_path)
    analysis = analyze_document(saved_path)
    
    permission_field = analysis.get("permission_number")
    permission_number = permission_field.get("value") if isinstance(permission_field, dict) else None
    if not permission_number:
        permission_number = extract_permission_number(extracted_text)

    document_record = PermissionDocument(
        file_name=upload.filename or saved_path.name,
        file_path=str(saved_path),
        extracted_text=extracted_text,
        permission_number=permission_number,
        extracted_json=analysis,
        created_by_user_id=current_user.user_id,
    )
    db.add(document_record)
    db.flush()
    _audit(
        db,
        current_user.user_id,
        "upload",
        "document",
        str(document_record.document_id),
        {"file_name": document_record.file_name, "permission_number": permission_number},
    )
    db.commit()
    db.refresh(document_record)

    return PermissionUploadResponse(
        document_id=document_record.document_id,
        permission_number=permission_number,
        extracted_text=extracted_text,
        analysis=analysis,
    )


@app.get("/documents/analysis", response_model=ExtractionResponse)
def preview_document_analysis(text: str, current_user: Freelancer = Depends(get_current_user)) -> ExtractionResponse:
    return ExtractionResponse(**analyze_document(text))


@app.get("/reports")
def list_reports() -> dict[str, list[Any]]:
    return {"reports": []}