from __future__ import annotations

import sys

# Force unbuffered UTF-8 output so every print() and log line appears
# immediately in the terminal regardless of how the process was launched.
# This must run before any other import.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=False)
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", line_buffering=False)

from pathlib import Path
from dotenv import load_dotenv
ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env", override=True)
load_dotenv(ROOT_DIR.parent / ".env", override=True)

import json
from datetime import datetime, timedelta
from typing import Any

from fastapi import Depends, FastAPI, File, Header, Form, HTTPException, UploadFile, status, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session

from .database import Base, engine, get_db
from .dependencies import get_template_service
from .models import AuditLog, Freelancer, Hlc, PermissionDocument, SessionToken, Valuer, HeaderTemplate, Template, CompletionCertificateTemplate
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
    TemplateUploadResponse,
    TemplateDetailResponse,
    ValuerCreate,
    ValuerUpdate,
    HeaderTemplateResponse,
    CompletionCertificateResponse,
    CompletionCertificateUpdate,
    MapSavedFieldsRequest,
    TemplateFieldsGetResponse,
)
from .security import create_token, hash_password, verify_password
from .services.documents import STORAGE_ROOT, analyze_document, extract_permission_number, extract_text_from_upload, save_upload, flatten_results
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
    
    try:
        from sqlalchemy import inspect, text
        inspector = inspect(engine)
        columns = [col["name"] for col in inspector.get_columns("templates")]
        if "header_template_id" not in columns:
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE templates ADD COLUMN header_template_id INTEGER REFERENCES header_templates(id)"))

        tf_columns = [col["name"] for col in inspector.get_columns("template_fields")]
        if "created_at" not in tf_columns:
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE template_fields ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL"))
        if "field_type" not in tf_columns:
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE template_fields ADD COLUMN field_type VARCHAR(50) DEFAULT 'dynamic' NOT NULL"))
        if "static_value" not in tf_columns:
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE template_fields ADD COLUMN static_value VARCHAR(1000)"))

        # One-time data migration for existing TemplateFields
        from .database import SessionLocal
        from .models import TemplateField, Template
        from .services.template_parser import classify_field_type

        with SessionLocal() as db:
            unmigrated = db.query(TemplateField).filter(
                TemplateField.field_type.notin_(["AUTO", "MANUAL", "SECTION"])
            ).all()
            if unmigrated:
                print(f"[Migration] Classifying and updating {len(unmigrated)} existing template fields...")
                for tf in unmigrated:
                    tf.field_type = classify_field_type(tf.field_name)
                db.commit()
                print("[Migration] Fields migration completed successfully.")

            # Migrate template_content_json for existing templates
            templates = db.query(Template).all()
            migrated_templates = 0
            for t in templates:
                content = t.template_content_json
                if not content or "sections" not in content:
                    continue
                modified = False
                
                def migrate_fields_rec(fields_list):
                    nonlocal modified
                    for f in fields_list:
                        curr_type = f.get("field_type")
                        if curr_type not in ("AUTO", "MANUAL", "SECTION"):
                            f["field_type"] = classify_field_type(f.get("label") or "")
                            modified = True
                        nested = f.get("nested_fields")
                        if nested:
                            migrate_fields_rec(nested)
                            
                for section in content["sections"]:
                    migrate_fields_rec(section.get("fields", []))
                
                if modified:
                    t.template_content_json = dict(content)
                    migrated_templates += 1
            if migrated_templates > 0:
                db.commit()
                print(f"[Migration] Migrated template_content_json for {migrated_templates} templates.")
    except Exception as e:
        print(f"Database migration error: {e}")

    try:
        from .models import CompletionCertificateTemplate
        from .database import SessionLocal
        with SessionLocal() as db:
            cert = db.query(CompletionCertificateTemplate).first()
            if not cert:
                default_text = (
                    "To\tDate:{Date}\n"
                    "STATE BANK OF INDIA\n"
                    "RACPC (HLC)\n"
                    "HYDERABAD.\n\n"
                    "                           COMPLETION CERTIFICATE\n\n"
                    "This is 1. {Owner Name},\n"
                    " S/O. {Father Name}\n"
                    "2. {Co-owner Name},\n"
                    " W/O. {Co-owner Husband Name}\n"
                    "Mobile:{Mobile Number}\n\n"
                    "Completed the {Property Description}, Constructed on Open Plot bearing No.{Plot No}, "
                    "admeasuring an extent of {Area Sq Yds} Sq.Yds or {Area Sq Mtrs} Sq.Mtrs, in Survey No's.{Survey Nos}, "
                    "having total built up area of {Built Up Area} Sq.Feet ({Built Up Area Details}), roof covered with R.C.C., "
                    "as shown in the Plan annexed herewith, situated at {Village} Village Under the Municipal Limits of "
                    "{Municipality} Municipality, {Mandal} Mandal, {District} District, Telangana State,Pin:{Pin Code}\n"
                    "We have inspected the Premises on {Inspection Date} and observed that the Building works and interior works "
                    "are completed and ready to occupy.\n\n"
                    "Note: \n"
                    "1) The subjected house is fully completed.\n"
                    "2) As on date of inspection this property was ready for occupation.\n"
                    "3) This certificate is issued for completion purpose only\n"
                    "4) This certificate is issued irrespective of valuation & plan approved."
                )
                db.add(CompletionCertificateTemplate(id=1, template_text=default_text))
                db.commit()
    except Exception as e:
        print(f"Error seeding completion certificate template: {e}")


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
    header_template_id: int | None = Form(default=None),
    file: UploadFile = File(...),
    template_service: TemplateService = Depends(get_template_service),
):
    try:
        return template_service.import_docx(
            template_key_id=template_key_id,
            template_name=template_name,
            template_bank=template_bank,
            upload=file,
            header_template_id=header_template_id,
        )
    except ValueError as e:
        if str(e) == "No template placeholders detected":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No template placeholders detected"
            )
        raise e


@app.post("/templates/import", response_model=TemplateImportResponse, status_code=status.HTTP_201_CREATED)
async def import_template(
    template_key_id: str = Form(...),
    template_name: str = Form(...),
    template_bank: str = Form(...),
    header_template_id: int | None = Form(default=None),
    file: UploadFile = File(...),
    template_service: TemplateService = Depends(get_template_service),
):
    try:
        print(f"[main.py] POST /templates/import - filename: {file.filename}, key: {template_key_id}, name: {template_name}")
        res = template_service.import_template(
            template_key_id=template_key_id,
            template_name=template_name,
            template_bank=template_bank,
            upload=file,
            header_template_id=header_template_id,
        )
        print(f"[main.py] POST /templates/import - SUCCESS")
        return res
    except ValueError as e:
        print(f"[main.py] POST /templates/import - ValueError: {e}")
        if str(e) == "No template placeholders detected":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No template placeholders detected"
            )
        raise e
    except Exception as e:
        print(f"[main.py] POST /templates/import - Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        raise e


@app.post("/templates/upload", response_model=TemplateUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_template(
    template_name: str = Form(...),
    file: UploadFile = File(...),
    template_service: TemplateService = Depends(get_template_service),
):
    import re
    template_key_id = re.sub(r"[^a-z0-9]+", "_", template_name.lower()).strip("_")
    if not template_key_id:
        template_key_id = "template"
    try:
        res = template_service.import_template(
            template_key_id=template_key_id,
            template_name=template_name,
            template_bank="General",
            upload=file,
            header_template_id=None,
        )
        template_id = res["template_id"]
        fields = template_service.get_template_fields(template_id, as_strings=True)
        return TemplateUploadResponse(
            template_id=template_id,
            template_name=res["template_name"],
            field_count=len(fields),
            fields=fields
        )
    except ValueError as e:
        if str(e) == "No template placeholders detected":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No template placeholders detected"
            )
        raise e


@app.get("/templates", response_model=list[TemplateListItem])
def list_templates(template_service: TemplateService = Depends(get_template_service)) -> list[dict[str, Any]]:
    templates = template_service.list_templates()
    for t in templates:
        t["field_count"] = template_service.get_template_field_count(t["template_id"])
    return templates


@app.get("/templates/{template_id}", response_model=TemplateDetailResponse)
def get_template(template_id: int, template_service: TemplateService = Depends(get_template_service)) -> dict[str, Any]:
    template = template_service.get_template(template_id)
    if template is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")
    
    fields = template_service.get_template_fields(template_id, as_strings=False)
    return {
        "id": template["id"],
        "name": template["template_name"],
        "field_count": len(fields),
        "fields": fields
    }


@app.get("/templates/{template_id}/fields", response_model=TemplateFieldsGetResponse)
def get_template_fields_endpoint(
    template_id: int,
    template_service: TemplateService = Depends(get_template_service)
) -> dict[str, Any]:
    template = template_service.get_template(template_id)
    if template is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")
    
    fields = template_service.get_template_fields(template_id, as_strings=False)
    return {
        "template_id": template_id,
        "template_name": template["template_name"],
        "fields": fields
    }


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
def generate_report(
    template_id: int,
    field_values: dict[str, Any],
    header_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
    template_service: TemplateService = Depends(get_template_service)
) -> dict[str, Any]:
    header_image_path = None
    if header_id:
        from .models import HeaderTemplate
        header_temp = db.get(HeaderTemplate, header_id)
        if header_temp:
            from pathlib import Path
            header_image_path = STORAGE_ROOT / "headers" / Path(header_temp.image_path).name
    else:
        # Fallback to template's default header
        template = template_service.repository.get_template(template_id)
        if template and template.header_template_id:
            from .models import HeaderTemplate
            header_temp = db.get(HeaderTemplate, template.header_template_id)
            if header_temp:
                from pathlib import Path
                header_image_path = STORAGE_ROOT / "headers" / Path(header_temp.image_path).name

    output_path = template_service.generate_report(template_id, field_values, header_image_path=header_image_path)
    try:
        relative_url = output_path.relative_to(STORAGE_ROOT).as_posix()
        report_url = f"/storage/{relative_url}"
    except ValueError:
        report_url = f"/storage/generated_reports/{output_path.name}"
    return {"report_url": report_url, "file_path": str(output_path)}


@app.post("/reports/generate/{template_id}")
async def generate_report_endpoint(
    template_id: int,
    header_id: int | None = Query(default=None),
    files: list[UploadFile] = File(...),
    db: Session = Depends(get_db),
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

    header_image_path = None
    if header_id:
        from .models import HeaderTemplate
        header_temp = db.get(HeaderTemplate, header_id)
        if header_temp:
            from pathlib import Path
            header_image_path = STORAGE_ROOT / "headers" / Path(header_temp.image_path).name
    elif template and template.header_template_id:
        from .models import HeaderTemplate
        header_temp = db.get(HeaderTemplate, template.header_template_id)
        if header_temp:
            from pathlib import Path
            header_image_path = STORAGE_ROOT / "headers" / Path(header_temp.image_path).name

    import uuid
    output_name = f"report_{uuid.uuid4().hex}.docx"
    generated_file = template_service.generate_report(template_id, field_values, output_name=output_name, header_image_path=header_image_path)

    return FileResponse(
        path=str(generated_file),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename="valuation_report.docx"
    )


@app.post("/documents/permission-number", response_model=PermissionUploadResponse)
async def get_permission_number(
    file: UploadFile | None = File(default=None),
    upload: UploadFile | None = File(default=None),
    template_id: int | None = Form(default=None),
    db: Session = Depends(get_db),
    current_user: Freelancer = Depends(get_current_user),
    template_service: TemplateService = Depends(get_template_service),
) -> PermissionUploadResponse:
    actual_file = file or upload
    if not actual_file:
        raise HTTPException(status_code=400, detail="No file uploaded")
        
    if template_id is None:
        raise HTTPException(status_code=400, detail="Please select a template before extraction.")
        
    from .models import Template
    template = db.get(Template, template_id)
    if not template:
        raise HTTPException(status_code=400, detail="Please select a template before extraction.")

    saved_path = save_upload(actual_file, "documents")
    extracted_text = extract_text_from_upload(saved_path)
    
    required_fields = template_service.get_template_required_fields(template_id)
    print(f"[Backend Preparation] Fetching fields for template_id={template_id}")
    print(f"[Backend Preparation] required_fields: {required_fields}")
        
    analysis = analyze_document(saved_path, required_fields)
    
    permission_number = None
    for item in analysis:
        if item.get("canonical_name") == "permission_number":
            permission_number = item.get("value")
            break
                
    if not permission_number:
        permission_number = extract_permission_number(extracted_text)

    document_record = PermissionDocument(
        file_name=actual_file.filename or saved_path.name,
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
        required_fields=required_fields,
    )


@app.get("/documents/analysis")
def preview_document_analysis(
    text: str,
    template_id: int | None = None,
    template_service: TemplateService = Depends(get_template_service),
    current_user: Freelancer = Depends(get_current_user)
) -> list[dict[str, Any]]:
    if template_id is None:
        raise HTTPException(status_code=400, detail="Please select a template before extraction.")
    required_fields = template_service.get_template_required_fields(template_id)
    return analyze_document(text, required_fields)


@app.get("/documents/{document_id}/download-json", response_model=dict[str, Any])
def download_document_json(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: Freelancer = Depends(get_current_user),
) -> dict[str, Any]:
    doc = db.get(PermissionDocument, document_id)
    if not doc or doc.created_by_user_id != current_user.user_id:
        raise HTTPException(status_code=404, detail="Document not found")
    return flatten_results(doc.extracted_json)


@app.get("/documents", response_model=list[dict[str, Any]])
def list_documents(
    db: Session = Depends(get_db),
    current_user: Freelancer = Depends(get_current_user),
) -> list[dict[str, Any]]:
    docs = db.query(PermissionDocument).filter(PermissionDocument.created_by_user_id == current_user.user_id).order_by(PermissionDocument.created_date.desc()).all()
    return [
        {
            "document_id": d.document_id,
            "file_name": d.file_name,
            "permission_number": d.permission_number,
            "created_at": d.created_date.isoformat() if d.created_date else None,
        }
        for d in docs
    ]


@app.put("/documents/{document_id}/analysis")
def update_document_analysis(
    document_id: int,
    payload: dict[str, Any],
    db: Session = Depends(get_db),
    current_user: Freelancer = Depends(get_current_user),
) -> dict[str, Any]:
    doc = db.get(PermissionDocument, document_id)
    if not doc or doc.created_by_user_id != current_user.user_id:
        raise HTTPException(status_code=404, detail="Document not found")
        
    current_list = list(doc.extracted_json) if isinstance(doc.extracted_json, list) else []
    canonical_to_item = {item.get("canonical_name"): item for item in current_list if isinstance(item, dict)}
    
    for k, v in payload.items():
        if k in canonical_to_item:
            canonical_to_item[k]["value"] = v
        else:
            new_item = {
                "canonical_name": k,
                "field_name": k.replace("_", " ").title(),
                "value": v,
                "confidence": 100
            }
            current_list.append(new_item)
            canonical_to_item[k] = new_item
            
    doc.extracted_json = current_list
    if "permission_number" in payload:
        doc.permission_number = payload["permission_number"]
        
    db.commit()
    db.refresh(doc)
    return {"message": "Document analysis updated successfully", "analysis": doc.extracted_json}


@app.post("/templates/{template_id}/map-saved-fields")
def map_saved_fields_endpoint(
    template_id: int,
    payload: MapSavedFieldsRequest,
    db: Session = Depends(get_db),
    current_user: Freelancer = Depends(get_current_user),
    template_service: TemplateService = Depends(get_template_service),
) -> dict[str, Any]:
    doc = db.get(PermissionDocument, payload.document_id)
    if not doc or doc.created_by_user_id != current_user.user_id:
        raise HTTPException(status_code=404, detail="Document not found")
        
    saved_values = flatten_results(doc.extracted_json)
    return template_service.map_saved_fields(template_id, saved_values)


@app.get("/reports")
def list_reports() -> dict[str, list[Any]]:
    return {"reports": []}


# Header Templates Endpoints
@app.get("/header-templates", response_model=list[HeaderTemplateResponse])
def list_header_templates(db: Session = Depends(get_db), current_user: Freelancer = Depends(get_current_user)) -> list[HeaderTemplate]:
    return db.query(HeaderTemplate).all()


@app.post("/header-templates", response_model=HeaderTemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_header_template(
    header_name: str = Form(...),
    is_active: bool = Form(default=True),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: Freelancer = Depends(get_current_user)
) -> HeaderTemplate:
    headers_dir = STORAGE_ROOT / "headers"
    headers_dir.mkdir(parents=True, exist_ok=True)
    
    import uuid
    from pathlib import Path
    suffix = Path(file.filename or "header.png").suffix.lower()
    if suffix not in {".png", ".jpg", ".jpeg"}:
        raise HTTPException(status_code=400, detail="Only JPG, JPEG, and PNG files are allowed")
        
    # 5MB size limit validation
    content = await file.read()
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File size must be less than 5MB")
    await file.seek(0)

    filename = f"{uuid.uuid4().hex}{suffix}"
    saved_path = headers_dir / filename
    
    with saved_path.open("wb") as buffer:
        import shutil
        shutil.copyfileobj(file.file, buffer)
        
    image_path = f"/storage/headers/{filename}"
    
    header = HeaderTemplate(
        header_name=header_name,
        image_path=image_path,
        is_active=is_active
    )
    db.add(header)
    db.commit()
    db.refresh(header)
    return header


@app.put("/header-templates/{header_id}", response_model=HeaderTemplateResponse)
async def update_header_template(
    header_id: int,
    header_name: str | None = Form(default=None),
    is_active: bool | None = Form(default=None),
    file: UploadFile | None = File(default=None),
    db: Session = Depends(get_db),
    current_user: Freelancer = Depends(get_current_user)
) -> HeaderTemplate:
    header = db.get(HeaderTemplate, header_id)
    if not header:
        raise HTTPException(status_code=404, detail="Header template not found")
        
    if header_name is not None:
        header.header_name = header_name
    if is_active is not None:
        header.is_active = is_active
        
    if file is not None:
        from pathlib import Path
        suffix = Path(file.filename or "header.png").suffix.lower()
        if suffix not in {".png", ".jpg", ".jpeg"}:
            raise HTTPException(status_code=400, detail="Only JPG, JPEG, and PNG files are allowed")
            
        # 5MB size limit validation
        content = await file.read()
        if len(content) > 5 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File size must be less than 5MB")
        await file.seek(0)

        try:
            old_path = STORAGE_ROOT / "headers" / Path(header.image_path).name
            if old_path.exists() and old_path.is_file():
                old_path.unlink()
        except Exception:
            pass
            
        headers_dir = STORAGE_ROOT / "headers"
        headers_dir.mkdir(parents=True, exist_ok=True)
        import uuid
        filename = f"{uuid.uuid4().hex}{suffix}"
        saved_path = headers_dir / filename
        
        with saved_path.open("wb") as buffer:
            import shutil
            shutil.copyfileobj(file.file, buffer)
            
        header.image_path = f"/storage/headers/{filename}"
        
    header.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(header)
    return header


@app.delete("/header-templates/{header_id}")
def delete_header_template(
    header_id: int,
    db: Session = Depends(get_db),
    current_user: Freelancer = Depends(get_current_user)
) -> dict[str, str]:
    header = db.get(HeaderTemplate, header_id)
    if not header:
        raise HTTPException(status_code=404, detail="Header template not found")
        
    try:
        from pathlib import Path
        img_file_path = STORAGE_ROOT / "headers" / Path(header.image_path).name
        if img_file_path.exists() and img_file_path.is_file():
            img_file_path.unlink()
    except Exception:
        pass
        
    db.query(Template).filter(Template.header_template_id == header_id).update({Template.header_template_id: None})
    
    db.delete(header)
    db.commit()
    return {"message": "Header template deleted"}


@app.get("/completion-certificate", response_model=CompletionCertificateResponse)
def get_completion_certificate(db: Session = Depends(get_db), current_user: Freelancer = Depends(get_current_user)) -> CompletionCertificateResponse:
    cert = db.query(CompletionCertificateTemplate).first()
    if not cert:
        default_text = "To\tDate:{Date}\nSTATE BANK OF INDIA\nRACPC (HLC)\nHYDERABAD.\n\n                           COMPLETION CERTIFICATE\n\nThis is 1. {Owner Name},\n S/O. {Father Name}\n2. {Co-owner Name},\n W/O. {Co-owner Husband Name}\nMobile:{Mobile Number}\n\nCompleted the {Property Description}, Constructed on Open Plot bearing No.{Plot No}, admeasuring an extent of {Area Sq Yds} Sq.Yds or {Area Sq Mtrs} Sq.Mtrs, in Survey No's.{Survey Nos}, having total built up area of {Built Up Area} Sq.Feet ({Built Up Area Details}), roof covered with R.C.C., as shown in the Plan annexed herewith, situated at {Village} Village Under the Municipal Limits of {Municipality} Municipality, {Mandal} Mandal, {District} District, Telangana State,Pin:{Pin Code}\nWe have inspected the Premises on {Inspection Date} and observed that the Building works and interior works are completed and ready to occupy.\n\nNote: \n1) The subjected house is fully completed.\n2) As on date of inspection this property was ready for occupation.\n3) This certificate is issued for completion purpose only\n4) This certificate is issued irrespective of valuation & plan approved."
        cert = CompletionCertificateTemplate(id=1, template_text=default_text)
        db.add(cert)
        db.commit()
        db.refresh(cert)
    return cert


@app.put("/completion-certificate", response_model=CompletionCertificateResponse)
def update_completion_certificate(
    payload: CompletionCertificateUpdate,
    db: Session = Depends(get_db),
    current_user: Freelancer = Depends(get_current_user)
) -> CompletionCertificateResponse:
    cert = db.query(CompletionCertificateTemplate).first()
    if not cert:
        cert = CompletionCertificateTemplate(id=1, template_text=payload.template_text)
        db.add(cert)
    else:
        cert.template_text = payload.template_text
        cert.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(cert)
    return cert