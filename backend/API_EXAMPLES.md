# API Request/Response Examples for Frontend & Dashboard Teams

## Overview
This document provides exact example JSON for all API endpoints. Share this with frontend (Members 2, 4, 6) and dashboard teams.

**Base URL:** `http://localhost:8000`  
**API Documentation:** `http://localhost:8000/docs` (Swagger UI)  
**Alternative Docs:** `http://localhost:8000/redoc` (ReDoc)

---

## 1. Health Check Endpoint

### Endpoint
```
GET /health
```

### Example Response
```json
{
  "status": "ok",
  "service": "legal-metrology-api"
}
```

---

## 2. Create a Scan (Member 2 - Image Upload)

### Endpoint
```
POST /scans
Content-Type: application/json
```

### Example Request
```json
{
  "product_name": "Sunflower Oil - Refined Premium",
  "image_url": "https://example.com/images/scan-001.jpg",
  "raw_ocr_text": "Sunflower Oil Refined\nMRP Rs. 250\nNet Quantity: 500 ml\nManufacturer: ABC Oils Ltd, Plot 123, Industrial Area, Mumbai, Pin 400001\nMfg Date: 15/02/2025\nBest Before: 14/02/2026\nCountry of Origin: MADE IN INDIA"
}
```

### Example Response (201 Created)
```json
{
  "id": "scan-005",
  "status": "pending",
  "product_name": "Sunflower Oil - Refined Premium",
  "image_url": "https://example.com/images/scan-001.jpg",
  "created_at": "2026-09-02T10:35:00+00:00"
}
```

---

## 3. Extract Fields from Scan (Member 2 - AI Processing)

### Endpoint
```
POST /scans/{scan_id}/extract
Content-Type: application/json
```

### Example Request
```json
{
  "raw_ocr_text": "Sunflower Oil Refined\nMRP Rs. 250\nNet Quantity: 500 ml\nManufacturer: ABC Oils Ltd, Plot 123, Industrial Area, Mumbai, Pin 400001\nMfg Date: 15/02/2025\nBest Before: 14/02/2026\nCountry of Origin: MADE IN INDIA"
}
```

### Example Response (200 OK)
```json
{
  "scan_id": "scan-005",
  "fields": [
    {
      "field_name": "product_name",
      "value": "Sunflower Oil Refined",
      "confidence": 0.94,
      "source_text": "Sunflower Oil Refined"
    },
    {
      "field_name": "mrp",
      "value": "250",
      "confidence": 0.97,
      "source_text": "MRP Rs. 250"
    },
    {
      "field_name": "net_quantity",
      "value": "500 ml",
      "confidence": 0.96,
      "source_text": "Net Quantity: 500 ml"
    },
    {
      "field_name": "manufacturer",
      "value": "ABC Oils Ltd, Plot 123, Industrial Area, Mumbai, Pin 400001",
      "confidence": 0.91,
      "source_text": "Manufacturer: ABC Oils Ltd, Plot 123, Industria..."
    },
    {
      "field_name": "mfg_date",
      "value": "15/02/2025",
      "confidence": 0.88,
      "source_text": "Mfg Date: 15/02/2025"
    },
    {
      "field_name": "exp_date",
      "value": "14/02/2026",
      "confidence": 0.88,
      "source_text": "Best Before: 14/02/2026"
    }
  ],
  "extracted_at": "2026-09-02T11:45:30.123456+00:00"
}
```

---

## 4. Get Scan Details (Member 4 - Dashboard Display)

### Endpoint
```
GET /scans/{scan_id}
```

### Example Response (200 OK)
```json
{
  "id": "scan-005",
  "status": "completed",
  "product_name": "Sunflower Oil - Refined Premium",
  "image_url": "https://example.com/images/scan-001.jpg",
  "created_at": "2026-09-02T10:35:00+00:00",
  "compliance_score": 60,
  "fields": [
    {
      "field_name": "product_name",
      "value": "Sunflower Oil Refined",
      "confidence": 0.94,
      "source_text": "Sunflower Oil Refined"
    },
    {
      "field_name": "mrp",
      "value": "250",
      "confidence": 0.97,
      "source_text": "MRP Rs. 250"
    },
    {
      "field_name": "net_quantity",
      "value": "500 ml",
      "confidence": 0.96,
      "source_text": "Net Quantity: 500 ml"
    },
    {
      "field_name": "manufacturer",
      "value": "ABC Oils Ltd, Plot 123, Industrial Area, Mumbai, Pin 400001",
      "confidence": 0.91,
      "source_text": "Manufacturer: ABC Oils Ltd, Plot 123, Industria..."
    },
    {
      "field_name": "mfg_date",
      "value": "15/02/2025",
      "confidence": 0.88,
      "source_text": "Mfg Date: 15/02/2025"
    },
    {
      "field_name": "exp_date",
      "value": "14/02/2026",
      "confidence": 0.88,
      "source_text": "Best Before: 14/02/2026"
    }
  ],
  "violations": [
    {
      "id": "vio-005-001",
      "scan_id": "scan-005",
      "rule_code": "LM-007",
      "severity": "minor",
      "description": "Country of origin not declared",
      "expected": "Country of origin statement",
      "actual": "Not detected",
      "field_name": "country_of_origin"
    }
  ]
}
```

---

## 5. List All Scans (Member 4 - Dashboard List View)

### Endpoint
```
GET /scans
```

### Example Response (200 OK)
```json
{
  "items": [
    {
      "id": "scan-005",
      "status": "completed",
      "product_name": "Sunflower Oil - Refined Premium",
      "image_url": "https://example.com/images/scan-001.jpg",
      "created_at": "2026-09-02T10:35:00+00:00"
    },
    {
      "id": "scan-004",
      "status": "completed",
      "product_name": "Basmati Rice Premium",
      "image_url": "https://example.com/images/scan-002.jpg",
      "created_at": "2026-09-02T09:20:00+00:00"
    },
    {
      "id": "scan-003",
      "status": "pending",
      "product_name": "Honey Natural Pure",
      "image_url": "https://example.com/images/scan-003.jpg",
      "created_at": "2026-09-02T08:15:00+00:00"
    }
  ],
  "total": 3
}
```

---

## 6. Get Scan Violations (Member 4 - Violation Analysis)

### Endpoint
```
GET /violations?scan_id=scan-005
```

### Example Response (200 OK)
```json
{
  "items": [
    {
      "id": "vio-005-001",
      "scan_id": "scan-005",
      "rule_code": "LM-007",
      "severity": "minor",
      "description": "Country of origin not declared",
      "expected": "Country of origin statement",
      "actual": "Not detected",
      "field_name": "country_of_origin"
    }
  ],
  "total": 1,
  "scan_id": "scan-005"
}
```

---

## 7. Generate Compliance Report (Member 6 - Inspector Report)

### Endpoint
```
POST /reports/{scan_id}
```

### Example Request
```
POST /reports/scan-005
(Empty body - no request payload needed)
```

### Example Response (201 Created)
```json
{
  "id": "rpt-003",
  "scan_id": "scan-005",
  "product_name": "Sunflower Oil - Refined Premium",
  "compliance_score": 60,
  "violation_count": 1,
  "status": "fail",
  "generated_at": "2026-09-02T09:15:00+00:00",
  "fields": [
    {
      "field_name": "product_name",
      "value": "Sunflower Oil Refined",
      "confidence": 0.94,
      "source_text": "Sunflower Oil Refined"
    },
    {
      "field_name": "mrp",
      "value": "250",
      "confidence": 0.97,
      "source_text": "MRP Rs. 250"
    },
    {
      "field_name": "net_quantity",
      "value": "500 ml",
      "confidence": 0.96,
      "source_text": "Net Quantity: 500 ml"
    },
    {
      "field_name": "manufacturer",
      "value": "ABC Oils Ltd, Plot 123, Industrial Area, Mumbai, Pin 400001",
      "confidence": 0.91,
      "source_text": "Manufacturer: ABC Oils Ltd, Plot 123, Industria..."
    },
    {
      "field_name": "mfg_date",
      "value": "15/02/2025",
      "confidence": 0.88,
      "source_text": "Mfg Date: 15/02/2025"
    },
    {
      "field_name": "exp_date",
      "value": "14/02/2026",
      "confidence": 0.88,
      "source_text": "Best Before: 14/02/2026"
    }
  ],
  "violations": [
    {
      "id": "vio-005-001",
      "scan_id": "scan-005",
      "rule_code": "LM-007",
      "severity": "minor",
      "description": "Country of origin not declared",
      "expected": "Country of origin statement",
      "actual": "Not detected",
      "field_name": "country_of_origin"
    }
  ],
  "inspector_notes": "Automated inspection — manual review recommended for manufacturer details.",
  "recommendations": [
    "Ensure manufacturer name and registered address are printed on the principal display panel.",
    "Add country of origin declaration per Legal Metrology (Packaged Commodities) Rules."
  ]
}
```

---

## 8. List All Reports (Member 6 - Report History)

### Endpoint
```
GET /reports
```

### Example Response (200 OK)
```json
{
  "items": [
    {
      "id": "rpt-003",
      "scan_id": "scan-005",
      "product_name": "Sunflower Oil - Refined Premium",
      "compliance_score": 60,
      "violation_count": 1,
      "status": "fail",
      "generated_at": "2026-09-02T09:15:00+00:00"
    },
    {
      "id": "rpt-002",
      "scan_id": "scan-004",
      "product_name": "Basmati Rice Premium",
      "compliance_score": 95,
      "violation_count": 0,
      "status": "pass",
      "generated_at": "2026-09-02T08:45:00+00:00"
    }
  ],
  "total": 2
}
```

---

## 9. Get Report Details (Member 6 - Single Report View)

### Endpoint
```
GET /reports/{report_id}
```

### Example Response (200 OK)
```json
{
  "id": "rpt-003",
  "scan_id": "scan-005",
  "product_name": "Sunflower Oil - Refined Premium",
  "compliance_score": 60,
  "violation_count": 1,
  "status": "fail",
  "generated_at": "2026-09-02T09:15:00+00:00",
  "fields": [
    {
      "field_name": "product_name",
      "value": "Sunflower Oil Refined",
      "confidence": 0.94,
      "source_text": "Sunflower Oil Refined"
    },
    {
      "field_name": "mrp",
      "value": "250",
      "confidence": 0.97,
      "source_text": "MRP Rs. 250"
    },
    {
      "field_name": "net_quantity",
      "value": "500 ml",
      "confidence": 0.96,
      "source_text": "Net Quantity: 500 ml"
    },
    {
      "field_name": "manufacturer",
      "value": "ABC Oils Ltd, Plot 123, Industrial Area, Mumbai, Pin 400001",
      "confidence": 0.91,
      "source_text": "Manufacturer: ABC Oils Ltd, Plot 123, Industria..."
    },
    {
      "field_name": "mfg_date",
      "value": "15/02/2025",
      "confidence": 0.88,
      "source_text": "Mfg Date: 15/02/2025"
    },
    {
      "field_name": "exp_date",
      "value": "14/02/2026",
      "confidence": 0.88,
      "source_text": "Best Before: 14/02/2026"
    }
  ],
  "violations": [
    {
      "id": "vio-005-001",
      "scan_id": "scan-005",
      "rule_code": "LM-007",
      "severity": "minor",
      "description": "Country of origin not declared",
      "expected": "Country of origin statement",
      "actual": "Not detected",
      "field_name": "country_of_origin"
    }
  ],
  "inspector_notes": "Automated inspection — manual review recommended for manufacturer details.",
  "recommendations": [
    "Ensure manufacturer name and registered address are printed on the principal display panel.",
    "Add country of origin declaration per Legal Metrology (Packaged Commodities) Rules."
  ]
}
```

---

## Violation Severity Levels

- **critical**: Fails legal metrology standards entirely (e.g., missing MRP)
- **major**: Significant compliance issues (e.g., no manufacturer info, no quantity)
- **minor**: Minor non-compliance (e.g., missing country of origin)

---

## Key Legal Metrology Rules

| Rule Code | Description | Severity |
|-----------|-------------|----------|
| LM-001 | MRP not found | CRITICAL |
| LM-002 | Net quantity not declared | MAJOR |
| LM-003 | Manufacturer name missing | MAJOR |
| LM-004 | Manufacturer address missing | MAJOR |
| LM-007 | Country of origin not declared | MINOR |

---

## Running the Server

```bash
cd /Users/srushti/Documents/SIH-repo/backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

**Access:**
- 🔵 Swagger Docs: http://localhost:8000/docs
- 🔵 ReDoc: http://localhost:8000/redoc
- 🔵 API Base: http://localhost:8000

---

## Data Flow

```
1. Image Upload (Frontend) 
   ↓
2. OCR Text Extraction (Member 2 Backend)
   ↓
3. CREATE SCAN → POST /scans
   ↓
4. EXTRACT FIELDS → POST /scans/{id}/extract
   ↓
5. VIEW RESULTS (Member 4 Dashboard) → GET /scans/{id}
   ↓
6. GENERATE REPORT (Member 6 Inspector) → POST /reports/{scan_id}
   ↓
7. DISPLAY REPORT (Member 6 Dashboard) → GET /reports/{report_id}
```

---

## Error Responses

### 404 Not Found
```json
{
  "detail": "Scan scan-999 not found"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error"
}
```

---

**Contact:** Legal Metrology API Team  
**Last Updated:** 2026-09-02  
**API Version:** 1.0.0
