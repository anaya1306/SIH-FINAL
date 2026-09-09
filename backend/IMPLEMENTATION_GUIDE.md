# AI Legal Metrology Inspection App - Backend Implementation Guide

## 📋 Project Overview

This is a **FastAPI-based backend** for an AI-powered legal metrology inspection application. The system automates the verification of packaged commodity labels against Indian Legal Metrology standards, detecting violations in product declarations (MRP, quantity, manufacturer info, etc.).

---

## ✅ What Has Been Completed

### 1. **Dependencies Setup** ✅
All required Python packages have been added to `requirements.txt`:
- **FastAPI** (0.141.0+): Modern web framework for building REST APIs
- **Uvicorn** (0.52.0+): ASGI server to run the FastAPI app
- **SQLAlchemy** (2.0.50+): ORM for database operations
- **Pydantic** (2.13.0+): Data validation and settings management
- **psycopg2-binary** (2.9.9+): PostgreSQL driver for database connections
- **python-dotenv**: Environment variable management
- **httpx**: For making HTTP requests in tests
- **pytest**: Testing framework

### 2. **Database Models** ✅
Defined in `app/db/models.py`:
- **ScanModel**: Stores product label scans with OCR text
- **ExtractedFieldModel**: Stores detected fields from labels
- **ViolationModel**: Stores compliance violations found
- **ReportModel**: Stores generated compliance reports

### 3. **Pydantic Schemas** ✅
Created response models in `app/schemas/`:
- **scan.py**: `ScanCreate`, `ScanResponse`, `ScanDetailResponse`, `ScanListResponse`, `ScanStatus`
- **field.py**: `ExtractedField`, `ExtractRequest`, `ExtractResponse`
- **violation.py**: `Violation`, `ViolationSeverity`, `ViolationListResponse`
- **report.py**: `ReportSummary`, `ReportDetail`, `ReportListResponse`, `ReportStatus`

### 4. **REST API Endpoints** ✅
Implemented in `app/api/`:

#### Health Check (`health.py`)
- `GET /health` - Server health status

#### Scans Management (`scans.py`)
- `POST /scans` - Create a new scan
- `GET /scans` - List all scans
- `GET /scans/{scan_id}` - Get scan details
- `POST /scans/{scan_id}/extract` - Extract fields from OCR text

#### Violations (`violations.py`)
- `GET /violations` - List all violations (with optional scan_id filter)
- `GET /scans/{scan_id}/violations` - Get violations for specific scan

#### Fields (`fields.py`)
- `GET /scans/{scan_id}/fields` - Get extracted fields for a scan

#### Reports (`reports.py`) **[NEW]**
- `POST /reports/{scan_id}` - Generate compliance report
- `GET /reports` - List all reports
- `GET /reports/{report_id}` - Get report details

### 5. **In-Memory Data Store** ✅
Implemented in `app/services/store.py`:
- Mock data storage for development/testing
- No database dependency initially
- `ScanRecord` and `ReportRecord` dataclasses for data structure
- Methods: `create_scan()`, `get_scan()`, `list_scans()`, `update_scan_fields()`, `generate_report()`, etc.

### 6. **AI Field Extraction Service** ✅
Implemented in `app/services/extraction.py`:
- **`extract_fields_from_text()`**: Uses regex patterns to extract:
  - Product name
  - MRP (Maximum Retail Price)
  - Net quantity
  - Manufacturer name
  - Manufacturing date
  - Expiry date
- **`check_violations()`**: Checks extracted fields against Legal Metrology rules
- **`compute_compliance_score()`**: Calculates product compliance score (0-100)

### 7. **Configuration Management** ✅
Defined in `app/config.py`:
- Database URL configuration (optional)
- CORS origins for frontend integration
- Settings management using Pydantic

### 8. **Main Application Entry Point** ✅ **[NEW]**
Created `main.py`:
- FastAPI app initialization with lifespan management
- CORS middleware for cross-origin requests
- Route registration for all API endpoints
- Root endpoint `/` showing API metadata

### 9. **Server Testing** ✅
Verified:
- ✅ Application imports successfully
- ✅ Server starts without errors
- ✅ `/health` endpoint returns correct response
- ✅ All endpoints are accessible

### 10. **API Documentation** ✅
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- Example request/response JSON in `API_EXAMPLES.md`

---

## 🎯 What Was Added (Last Session)

### New Files Created:
1. **`main.py`** - FastAPI application entry point
2. **`app/api/reports.py`** - Reports API endpoints
3. **`app/api/__init__.py`** - API module initialization
4. **`API_EXAMPLES.md`** - Complete API examples for teams
5. **`IMPLEMENTATION_GUIDE.md`** - This file

### Key Features Added:
- Complete Reports API (generate, list, retrieve)
- Full CORS support for frontend integration
- App lifespan management (startup/shutdown logs)
- Comprehensive API documentation

---

## 🏗️ Project Structure

```
backend/
├── main.py                          # ✅ FastAPI application entry point
├── requirements.txt                 # ✅ Python dependencies
├── .env.example                     # Environment variable template
├── API_EXAMPLES.md                  # ✅ Complete API examples
├── IMPLEMENTATION_GUIDE.md          # ✅ This file
│
└── app/
    ├── __init__.py                  
    ├── config.py                    # ✅ Configuration settings
    │
    ├── api/                         # REST API endpoints
    │   ├── __init__.py              # ✅ Module initialization
    │   ├── health.py                # ✅ Health check endpoint
    │   ├── scans.py                 # ✅ Scan management
    │   ├── violations.py            # ✅ Violations API
    │   ├── fields.py                # ✅ Fields retrieval
    │   └── reports.py               # ✅ Reports API [NEW]
    │
    ├── db/                          # Database layer
    │   ├── __init__.py
    │   ├── models.py                # ✅ SQLAlchemy models
    │   └── session.py               # Database session
    │
    ├── schemas/                     # Pydantic response models
    │   ├── __init__.py
    │   ├── scan.py                  # ✅ Scan schemas
    │   ├── field.py                 # ✅ Field schemas
    │   ├── violation.py             # ✅ Violation schemas
    │   └── report.py                # ✅ Report schemas
    │
    └── services/                    # Business logic
        ├── __init__.py
        ├── store.py                 # ✅ In-memory data store
        ├── extraction.py            # ✅ AI field extraction
        └── seed_data.py             # Sample data

└── tests/                           # Unit tests (to be completed)
```

---

## 🚀 How to Run the Application

### Step 1: Navigate to Backend Directory
```bash
cd /Users/srushti/Documents/SIH-repo/backend
```

### Step 2: Install Dependencies (First Time Only)
```bash
pip install -r requirements.txt
```

### Step 3: Start the Server
```bash
# Option 1: With auto-reload (development)
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Option 2: Using main.py directly
python main.py

# Option 3: Production mode (no reload)
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

### Step 4: Access the API
- **Swagger Docs:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **API Base URL:** http://localhost:8000
- **Health Check:** http://localhost:8000/health

---

## 📊 API Workflow

### Complete Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│                  INSPECTION WORKFLOW                        │
└─────────────────────────────────────────────────────────────┘

1. UPLOAD PRODUCT IMAGE (Member 2 - Frontend)
   ↓
   Frontend app captures product label image and performs OCR
   ↓
2. CREATE SCAN (POST /scans)
   Request:  { product_name, image_url, raw_ocr_text }
   Response: { id, status: pending, created_at }
   ↓
3. EXTRACT FIELDS (POST /scans/{scan_id}/extract)
   AI Service: Regex patterns identify label fields
   Response:  { fields[], violations[], compliance_score }
   ↓
4. VIEW SCAN RESULTS (Member 4 - Dashboard)
   GET /scans/{scan_id}
   Response: Full scan details with extracted fields and violations
   ↓
5. ANALYZE VIOLATIONS (Member 4)
   GET /violations?scan_id=scan-005
   Response: List of detected compliance issues with severity
   ↓
6. GENERATE REPORT (Member 6 - Inspector)
   POST /reports/{scan_id}
   Response: Compliance report with recommendations
   ↓
7. VIEW REPORT (Member 6 - Dashboard)
   GET /reports/{report_id}
   Response: Full report with inspector notes and recommendations
```

---

## 🔍 Example API Usage

### Create a Scan
```bash
curl -X POST "http://localhost:8000/scans" \
  -H "Content-Type: application/json" \
  -d '{
    "product_name": "Sunflower Oil Premium",
    "image_url": "https://example.com/oil.jpg",
    "raw_ocr_text": "Sunflower Oil\nMRP Rs. 250\nNet Qty: 500ml"
  }'
```

### Extract Fields and Detect Violations
```bash
curl -X POST "http://localhost:8000/scans/scan-005/extract" \
  -H "Content-Type: application/json" \
  -d '{
    "raw_ocr_text": "Sunflower Oil\nMRP Rs. 250\nNet Qty: 500ml\nMade in India"
  }'
```

### Generate Report
```bash
curl -X POST "http://localhost:8000/reports/scan-005"
```

### Get All Reports
```bash
curl -X GET "http://localhost:8000/reports"
```

See **API_EXAMPLES.md** for complete examples with all request/response formats.

---

## 👥 Team Assignments & Responsibilities

### Member 2 - Image Processing & Field Extraction
- **Tasks:**
  - Capture product label images
  - Perform OCR on images to get text
  - Call `POST /scans` to create scan
  - Call `POST /scans/{id}/extract` to extract fields
- **Key Endpoints:**
  - `POST /scans`
  - `POST /scans/{scan_id}/extract`

### Member 4 - Dashboard & Visualization
- **Tasks:**
  - Display list of scans
  - Show scan details and extracted fields
  - Visualize violations with severity
  - Display compliance score
- **Key Endpoints:**
  - `GET /scans` (list)
  - `GET /scans/{scan_id}` (details)
  - `GET /violations?scan_id=X`

### Member 6 - Inspector Reports
- **Tasks:**
  - Generate compliance reports
  - Add inspector notes
  - View recommendations
  - Generate report history
- **Key Endpoints:**
  - `POST /reports/{scan_id}` (generate)
  - `GET /reports` (list)
  - `GET /reports/{report_id}` (details)

---

## 📝 Legal Metrology Rules Implemented

The system checks for compliance with these key rules:

| Rule | Description | Severity | Field |
|------|-------------|----------|-------|
| LM-001 | MRP must be displayed | CRITICAL | mrp |
| LM-002 | Net quantity must be declared | MAJOR | net_quantity |
| LM-003 | Manufacturer name required | MAJOR | manufacturer |
| LM-004 | Manufacturer address needed | MAJOR | manufacturer_address |
| LM-007 | Country of origin required | MINOR | country_of_origin |

---

## 🗄️ Data Models

### ScanRecord
```python
{
  "id": "scan-005",              # Unique scan ID
  "status": "completed",          # pending, processing, completed, failed
  "product_name": "Oil Premium",
  "image_url": "https://...",
  "raw_ocr_text": "...",
  "created_at": "2026-09-02T...",
  "fields": [...],                # Extracted fields
  "violations": [...],            # Detected violations
  "compliance_score": 85          # 0-100 score
}
```

### ExtractedField
```python
{
  "field_name": "mrp",
  "value": "250",
  "confidence": 0.97,             # 0.0-1.0 confidence score
  "source_text": "MRP Rs. 250"
}
```

### Violation
```python
{
  "id": "vio-005-001",
  "scan_id": "scan-005",
  "rule_code": "LM-001",
  "severity": "critical",         # critical, major, minor
  "description": "MRP not found",
  "expected": "MRP with prefix",
  "actual": "Not detected",
  "field_name": "mrp"
}
```

### Report
```python
{
  "id": "rpt-003",
  "scan_id": "scan-005",
  "compliance_score": 85,
  "violation_count": 1,
  "status": "fail",               # pass, fail, review
  "generated_at": "2026-09-02T...",
  "inspector_notes": "...",
  "recommendations": [...]
}
```

---

## 🔧 Configuration

Edit `.env` file (copy from `.env.example`):

```env
# App Configuration
APP_NAME=legal-metrology-api

# Database (Optional - defaults to in-memory store)
# DATABASE_URL=postgresql://user:password@localhost:5432/legal_metrology

# CORS Origins for frontend
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

---

## 🧪 Testing

### Health Check
```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "ok",
  "service": "legal-metrology-api"
}
```

### Run Unit Tests (Future)
```bash
pytest tests/
```

---

## 📚 Response Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request |
| 404 | Not Found |
| 500 | Internal Server Error |

---

## 🔐 Security Features (Future)

- [ ] Authentication (JWT tokens)
- [ ] Authorization (Role-based access control)
- [ ] Input validation (Pydantic models)
- [ ] CORS protection
- [ ] Rate limiting
- [ ] Database encryption

---

## 📈 Performance Considerations

**Current State (Day 1):**
- In-memory data store (no persistence)
- Suitable for development and testing
- Max ~1000 scans before memory issues

**Next Steps:**
1. Connect to PostgreSQL database
2. Add database indexing
3. Implement caching (Redis)
4. Add background job processing (Celery)
5. Horizontal scaling with load balancer

---

## 🐛 Troubleshooting

### Issue: `ModuleNotFoundError: No module named 'fastapi'`
**Solution:** Install dependencies
```bash
pip install -r requirements.txt
```

### Issue: Port 8000 already in use
**Solution:** Use different port or kill existing process
```bash
# Use different port
python -m uvicorn main:app --port 8001

# Or kill existing process
lsof -ti:8000 | xargs kill -9
```

### Issue: CORS errors in frontend
**Solution:** Check `.env` CORS_ORIGINS configuration
```env
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

### Issue: Database connection fails
**Solution:** Check DATABASE_URL or use in-memory store
```env
# Unset this to use in-memory store (development)
# DATABASE_URL=postgresql://...
```

---

## 📞 Next Steps

1. **Connect Database** - Migrate from in-memory to PostgreSQL
2. **Add Authentication** - Implement JWT token-based auth
3. **Frontend Integration** - Connect with React/Vue frontend
4. **Advanced AI** - Implement actual OCR (Tesseract/AWS Textract)
5. **Mobile App** - Add mobile inspection app
6. **Reports Export** - PDF/Excel report generation
7. **Notifications** - Email alerts for violations

---

## 👨‍💼 Support & Documentation

- **API Docs:** http://localhost:8000/docs
- **Examples:** See `API_EXAMPLES.md`
- **Issues:** Report to team lead
- **Questions:** Check project README

---

## 📅 Release Information

- **Version:** 1.0.0 (MVP)
- **Release Date:** 2026-09-02
- **Status:** ✅ In Development
- **Last Updated:** 2026-09-02

---

## 📄 License & Credits

**Project:** AI Legal Metrology Inspection System  
**Team:** Member 2, Member 4, Member 6  
**Backend Framework:** FastAPI  
**Database:** SQLAlchemy + PostgreSQL  
**Deployment:** Uvicorn ASGI Server

---

**End of Implementation Guide**
