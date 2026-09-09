from fastapi import FastAPI

from app.api.auth import router as auth_router
from app.api.rbac import router as rbac_router
from app.api.storage import router as storage_router
from app.api.admin import router as admin_router
from app.api.audit import router as audit_router
from app.db.database import Base, engine
from app.db import models
from app.db import audit


Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="AI-Assisted Legal Metrology Inspection System",
    description="Authentication, RBAC and Security API",
    version="1.0.0"
)


app.include_router(auth_router)
app.include_router(rbac_router)
app.include_router(storage_router)
app.include_router(admin_router)
app.include_router(audit_router)

@app.get("/")
def root():
    return {
        "message": "Legal Metrology Authentication API is running"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }