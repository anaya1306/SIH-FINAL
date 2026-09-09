from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, fields, health, scans, violations, reports
from app.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage app startup and shutdown."""
    # Startup
    print(f"🚀 Starting {settings.app_name}...")
    yield
    # Shutdown
    print(f"🛑 Shutting down {settings.app_name}...")


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="AI Legal Metrology Inspection API",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Add CORS middleware (must be before routers)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(scans.router)
app.include_router(violations.router)
app.include_router(fields.router)
app.include_router(reports.router)


@app.get("/")
def root():
    return {
        "app": settings.app_name,
        "version": "1.0.0",
        "docs_url": "/docs",
        "redoc_url": "/redoc",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
