# Quick Start Guide for Team Members

## 🚀 Start the Server (Everyone)

```bash
cd /Users/srushti/Documents/SIH-repo/backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

**What this does:**
- Starts the backend server on port 8000
- Automatically reloads on file changes
- Enables debug mode for development

---

## 📖 Access API Documentation

Open your browser to one of these URLs:

### Swagger UI (Interactive Testing) ⭐ **RECOMMENDED**
```
http://localhost:8000/docs
```
- Test all endpoints directly from browser
- See request/response examples
- Auto-generated from code

### ReDoc (Read-only Documentation)
```
http://localhost:8000/redoc
```
- Clean, searchable documentation
- Good for reference

### API Root
```
http://localhost:8000
```
- See basic API info

---

## 👤 Member 2 - Image Upload & AI Processing

### Your Job
Process product images and extract label information

### API You'll Use

**1. Create a Scan**
```bash
curl -X POST "http://localhost:8000/scans" \
  -H "Content-Type: application/json" \
  -d '{
    "product_name": "Sunflower Oil Premium 500ml",
    "image_url": "https://example.com/images/oil-001.jpg",
    "raw_ocr_text": "Sunflower Oil\nMRP Rs. 250\nNet Qty: 500 ml\nMfg: 15/02/2025\nExp: 14/02/2026"
  }'
```

**Response** (201 Created):
```json
{
  "id": "scan-005",
  "status": "pending",
  "product_name": "Sunflower Oil Premium 500ml",
  "image_url": "https://example.com/images/oil-001.jpg",
  "created_at": "2026-09-02T10:35:00+00:00"
}
```

**2. Extract Fields from OCR Text**
```bash
curl -X POST "http://localhost:8000/scans/scan-005/extract" \
  -H "Content-Type: application/json" \
  -d '{
    "raw_ocr_text": "Sunflower Oil\nMRP Rs. 250\nNet Qty: 500 ml\nManufacturer: ABC Oils Ltd\nMfg: 15/02/2025\nExp: 14/02/2026\nMade in India"
  }'
```

**Response** (200 OK):
```json
{
  "scan_id": "scan-005",
  "fields": [
    {
      "field_name": "product_name",
      "value": "Sunflower Oil",
      "confidence": 0.94,
      "source_text": "Sunflower Oil"
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
      "source_text": "Net Qty: 500 ml"
    },
    {
      "field_name": "manufacturer",
      "value": "ABC Oils Ltd",
      "confidence": 0.91,
      "source_text": "Manufacturer: ABC Oils Ltd"
    },
    {
      "field_name": "mfg_date",
      "value": "15/02/2025",
      "confidence": 0.88,
      "source_text": "Mfg: 15/02/2025"
    },
    {
      "field_name": "exp_date",
      "value": "14/02/2026",
      "confidence": 0.88,
      "source_text": "Exp: 14/02/2026"
    }
  ],
  "extracted_at": "2026-09-02T11:45:30.123456+00:00"
}
```

### What Gets Extracted
- ✅ Product name
- ✅ MRP (Maximum Retail Price)
- ✅ Net quantity
- ✅ Manufacturer name
- ✅ Manufacturing date
- ✅ Expiry date

### How to Debug
1. Check if OCR text is being sent correctly
2. Look at confidence scores - if low, OCR text might be unclear
3. Check extracted fields match your OCR output
4. See violations in the response

---

## 📊 Member 4 - Dashboard & Visualization

### Your Job
Display scan results and violations on dashboard

### API You'll Use

**1. Get All Scans (For List View)**
```bash
curl "http://localhost:8000/scans"
```

**Response**:
```json
{
  "items": [
    {
      "id": "scan-005",
      "status": "completed",
      "product_name": "Sunflower Oil Premium",
      "image_url": "https://example.com/images/oil-001.jpg",
      "created_at": "2026-09-02T10:35:00+00:00"
    },
    {
      "id": "scan-004",
      "status": "completed",
      "product_name": "Basmati Rice",
      "image_url": "https://example.com/images/rice-001.jpg",
      "created_at": "2026-09-02T09:20:00+00:00"
    }
  ],
  "total": 2
}
```

**2. Get Scan Details (For Detail View)**
```bash
curl "http://localhost:8000/scans/scan-005"
```

**Response**:
```json
{
  "id": "scan-005",
  "status": "completed",
  "product_name": "Sunflower Oil Premium",
  "image_url": "https://example.com/images/oil-001.jpg",
  "created_at": "2026-09-02T10:35:00+00:00",
  "compliance_score": 60,
  "fields": [
    {
      "field_name": "product_name",
      "value": "Sunflower Oil",
      "confidence": 0.94,
      "source_text": "Sunflower Oil"
    },
    {
      "field_name": "mrp",
      "value": "250",
      "confidence": 0.97,
      "source_text": "MRP Rs. 250"
    }
    // ... more fields
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

**3. Get Violations for a Scan**
```bash
curl "http://localhost:8000/violations?scan_id=scan-005"
```

**Response**:
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

### What to Display

**List View (All Scans)**
- Scan ID
- Product name
- Status (completed/pending/failed)
- Created date
- Product image thumbnail

**Detail View (Single Scan)**
- All of list view + detail
- Compliance score (color coded: Red <50, Yellow 50-80, Green >80)
- All extracted fields with confidence scores
- All violations with severity indicators
  - 🔴 CRITICAL (LM-001)
  - 🟡 MAJOR (LM-002, LM-003, LM-004)
  - 🟢 MINOR (LM-007)

### Severity Levels
- **CRITICAL** (Red): Fails legal requirements entirely
- **MAJOR** (Orange): Significant compliance issues
- **MINOR** (Yellow): Minor non-compliance

---

## 📋 Member 6 - Inspector Reports

### Your Job
Generate compliance reports and add inspector notes

### API You'll Use

**1. Generate Report**
```bash
curl -X POST "http://localhost:8000/reports/scan-005"
```

**Response** (201 Created):
```json
{
  "id": "rpt-003",
  "scan_id": "scan-005",
  "product_name": "Sunflower Oil Premium",
  "compliance_score": 60,
  "violation_count": 1,
  "status": "fail",
  "generated_at": "2026-09-02T09:15:00+00:00",
  "fields": [
    // ... all extracted fields
  ],
  "violations": [
    // ... all violations
  ],
  "inspector_notes": "Automated inspection — manual review recommended for manufacturer details.",
  "recommendations": [
    "Ensure manufacturer name and registered address are printed on the principal display panel.",
    "Add country of origin declaration per Legal Metrology (Packaged Commodities) Rules."
  ]
}
```

**2. List All Reports**
```bash
curl "http://localhost:8000/reports"
```

**Response**:
```json
{
  "items": [
    {
      "id": "rpt-003",
      "scan_id": "scan-005",
      "product_name": "Sunflower Oil Premium",
      "compliance_score": 60,
      "violation_count": 1,
      "status": "fail",
      "generated_at": "2026-09-02T09:15:00+00:00"
    },
    {
      "id": "rpt-002",
      "scan_id": "scan-004",
      "product_name": "Basmati Rice",
      "compliance_score": 95,
      "violation_count": 0,
      "status": "pass",
      "generated_at": "2026-09-02T08:45:00+00:00"
    }
  ],
  "total": 2
}
```

**3. Get Report Details**
```bash
curl "http://localhost:8000/reports/rpt-003"
```

**Response**: Same as Generate Report response above

### What to Display

**Report Summary**
- Report ID
- Product name
- Compliance status (PASS/FAIL/REVIEW)
- Compliance score
- Violation count
- Generated date

**Report Details**
- All summary info
- Full violations list with detailed info
- Inspector notes
- Actionable recommendations
- All extracted fields for reference

### Inspector Notes
- Automatically generated based on violations
- Can be customized for serious cases
- Used for manual follow-up

### Recommendations
- Auto-generated based on violations found
- List of corrective actions for manufacturer
- Based on Legal Metrology rules

---

## ⚡ Quick Commands Reference

### Health Check
```bash
curl http://localhost:8000/health
```

### Create Scan (Member 2)
```bash
curl -X POST http://localhost:8000/scans \
  -H "Content-Type: application/json" \
  -d '{"product_name":"Oil","image_url":"url","raw_ocr_text":"text"}'
```

### Extract Fields (Member 2)
```bash
curl -X POST http://localhost:8000/scans/scan-005/extract \
  -H "Content-Type: application/json" \
  -d '{"raw_ocr_text":"extracted text"}'
```

### Get Scans (Member 4)
```bash
curl http://localhost:8000/scans
```

### Get Scan Detail (Member 4)
```bash
curl http://localhost:8000/scans/scan-005
```

### Get Violations (Member 4)
```bash
curl http://localhost:8000/violations?scan_id=scan-005
```

### Generate Report (Member 6)
```bash
curl -X POST http://localhost:8000/reports/scan-005
```

### Get Reports (Member 6)
```bash
curl http://localhost:8000/reports
```

### Get Report Detail (Member 6)
```bash
curl http://localhost:8000/reports/rpt-003
```

---

## 🐛 Common Issues & Solutions

### Issue: `Connection refused` on http://localhost:8000
**Solution:** Make sure server is running
```bash
cd /Users/srushti/Documents/SIH-repo/backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Issue: `ModuleNotFoundError` when starting server
**Solution:** Install dependencies
```bash
pip install -r requirements.txt
```

### Issue: Server returns 404 for endpoint
**Solution:** Check endpoint path and HTTP method (GET/POST)

### Issue: JSON parsing error in response
**Solution:** Check Content-Type header is `application/json`

---

## 📞 Need Help?

1. **Check Swagger Docs:** http://localhost:8000/docs - Try endpoints there
2. **Review Examples:** Check `API_EXAMPLES.md` for complete examples
3. **Read Guide:** Check `IMPLEMENTATION_GUIDE.md` for detailed info
4. **Test in Swagger:** Use Swagger UI to test and debug
5. **Check Server Logs:** Look at terminal output for errors

---

## 💡 Tips for Frontend Integration

1. **Use Swagger to Understand:** Open `/docs` and explore all endpoints
2. **Test with Curl First:** Debug API before connecting frontend
3. **Handle Errors:** Check for 404/400/500 responses
4. **Set Headers:** Always send `Content-Type: application/json`
5. **Use CORS Origins:** Backend is configured for localhost:3000 and localhost:5173

---

## 📚 Additional Documentation

- **Full Implementation Guide:** `IMPLEMENTATION_GUIDE.md`
- **Complete API Examples:** `API_EXAMPLES.md`
- **API Swagger Docs:** http://localhost:8000/docs
- **Project Structure:** See directory listing above

---

**Last Updated:** 2026-09-02  
**Backend Version:** 1.0.0  
**Status:** ✅ Production Ready
