# Home Loan Valuation AI Hub Management System

A production-grade, template-driven AI automation platform designed for bank valuation professionals and freelancers. The platform automates OCR text extraction from legal property documents, maps extracted fields into standardized banking schemas, dynamically manages valuer letterhead assets, and generates high-fidelity DOCX valuation reports preserving 100% of original Microsoft Word document formatting.

---

## Key System Architecture & Features

### 1. Production DOCX Rendering Engine (`app/services/docx/`)
Treats uploaded bank DOCX templates as the absolute source of truth. Rather than recreating tables or cloning OpenXML structures, the engine performs **in-place character-stream text replacement on existing XML runs**:
- **`TemplateRenderer` (`placeholder_engine.py`)**: Reconstructs paragraph character maps `(run_object, local_char_idx)` to substitute strict double-curly bracket placeholders (`{{placeholder_name}}`) in-place, preserving font family (`font.name`), size (`font.size`), bold/italic styling, text colors, and paragraph alignments.
- **`HeaderEngine` (`header_engine.py`)**: Replaces the existing letterhead region situated before the first valuation table on Page 1 without shifting content or introducing extra blank lines.
- **`CertificateEngine` (`certificate_engine.py`)**: Renders customizable completion certificates immediately below the header image and immediately before valuation tables, dynamically resolving mail-merge placeholders (`{{owner_name}}`, `{{village}}`, `{{inspection_date}}`).
- **`ValidationEngine` (`validation_engine.py`)**: Enforces structural benchmark guards verifying that section, table, row, and cell geometries match the original template 100% while confirming zero unmapped `{{...}}` placeholders remain.

### 2. Header Template Management
- Independent, reusable letterhead banner asset library managed separately from template records.
- Supports atomic default header selection (`is_default`), active toggles (`is_active`), display ordering (`display_order`), and Pillow-driven image dimension extraction (`image_width`, `image_height`).
- Protected backend deletion locks preventing active default headers from being removed.

### 3. Completion Certificate Engine
- First-class, template-driven boilerplate document component managed centrally via database schema (`completion_certificate_templates`).
- Fully customizable from the user interface without requiring code modifications or server redeployments.

### 4. OCR & Document Intelligence
- Automated document analysis and text extraction from permission document uploads (PDF/Images).
- Smart canonical field mapping matching extracted OCR values (`owner_name`, `survey_number`, `property_address`, `plot_number`) against template field schemas.

### 5. Document Workspace & Review Workflow
- Guided 4-step wizard:
  1. *Select Bank Template*
  2. *Upload Property Permission Documents*
  3. *Extract & Review Field Values* (with manual override capabilities)
  4. *Select Letterhead & Compile Valuation Report*

---

## Technology Stack

- **Backend Framework**: Python 3.10+, FastAPI, Uvicorn
- **ORM & Database**: SQLAlchemy (SQLite for local development, PostgreSQL compatible)
- **Document & Image Processing**: python-docx, Pillow (PIL), PyPDF2 / pdfplumber
- **Frontend Framework**: React 18, Vite
- **Styling & UI**: Tailwind CSS, Vanilla CSS custom tokens

---

## Directory Structure

```text
e:/home/
├── backend/
│   ├── app/
│   │   ├── main.py                     # FastAPI application routes & startup migrations
│   │   ├── models.py                   # SQLAlchemy ORM database models
│   │   ├── schemas.py                  # Pydantic request/response validation schemas
│   │   ├── dependencies.py             # FastAPI dependency injection providers
│   │   ├── repositories/               # Database repository layer
│   │   │   ├── header_repository.py    # Letterhead DB operations
│   │   │   └── template_repository.py  # Bank template DB operations
│   │   └── services/                   # Core business & document processing logic
│   │       ├── docx/                   # Zero-loss DOCX Rendering Package
│   │       │   ├── placeholder_engine.py # Character-stream TemplateRenderer
│   │       │   ├── header_engine.py    # Letterhead replacement HeaderEngine
│   │       │   ├── certificate_engine.py # Mail-merge CertificateEngine
│   │       │   └── validation_engine.py  # Structural benchmark guards
│   │       ├── report_generator.py     # Orchestration layer for report generation
│   │       ├── header_service.py       # Letterhead business rules & validation
│   │       ├── template_service.py     # Template mapping & management
│   │       ├── ocr_engine.py           # Document OCR extraction pipeline
│   │       └── image_utils.py          # Pillow dimension & UUID file helpers
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.jsx                     # Core React workspace application
│   │   ├── components/
│   │   │   ├── HeaderManagement.jsx    # Valuer letterhead management panel
│   │   │   ├── HeaderSelector.jsx      # Workspace Step 4 letterhead selector
│   │   │   └── CompletionCertificateManagement.jsx # Certificate template editor
│   │   └── index.css                   # Global styles & design system tokens
│   └── package.json
└── README.md
```

---

## API Endpoints Summary

### Report & Document Workflows
- `POST /templates/{id}/generate-report`: Consumes JSON payload containing `field_values` and `rendering_options` (`header_id`, `certificate_enabled`) to generate a valuation report.
- `POST /documents/permission-number`: Uploads permission document, extracts OCR text, and matches template required fields.
- `PUT /documents/{id}/analysis`: Updates extracted field values with manual reviewer corrections.

### Letterhead Asset Management
- `GET /header-templates`: Retrieves all letterheads ordered by `display_order`.
- `POST /header-templates`: Uploads a new letterhead graphic (PNG/JPG, max 5MB).
- `PUT /header-templates/{id}/set-default`: Atomically sets specified letterhead as default.
- `DELETE /header-templates/{id}`: Deletes letterhead asset (protected for active defaults).

### Completion Certificate Management
- `GET /completion-certificate`: Retrieves current completion certificate template.
- `PUT /completion-certificate`: Updates completion certificate text template with mail-merge placeholders.

---

## Setup & Local Development

### 1. Backend Setup (Python / FastAPI)

```powershell
# Navigate to project root
Set-Location E:\home

# Activate virtual environment (Windows PowerShell)
.\.venv\Scripts\Activate.ps1

# Navigate to backend and install dependencies
Set-Location .\backend
pip install -r requirements.txt

# Run FastAPI development server
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### 2. Frontend Setup (React / Vite)

```powershell
# Navigate to frontend directory in a new terminal
Set-Location E:\home\frontend

# Install node dependencies
npm install

# Launch Vite development server
npm run dev
```

The frontend application will be accessible at `http://localhost:5173` and connected to the backend API at `http://127.0.0.1:8000`.
