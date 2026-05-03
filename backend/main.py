"""
Zentox Aesthetics CRM — FastAPI Backend
HIPAA-compliant internal API for Streamlit frontend.
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from backend.config import get_settings
from backend.routers import (
    auth_router,
    patients,
    appointments,
    pipeline,
    kpi,
    services,
    integrations,
    financials,
    staff,
    inventory,
    agents,
)

settings = get_settings()

app = FastAPI(
    title="Zentox Aesthetics CRM API",
    description="Internal CRM & financial model for Zentox Aesthetics — HIPAA compliant.",
    version="1.0.0",
    docs_url="/docs" if settings.debug else None,   # hide Swagger in production
    redoc_url="/redoc" if settings.debug else None,
)

# CORS — only allow the Streamlit frontend origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.allowed_origins.split(",")],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
    response.headers["Cache-Control"] = "no-store"
    return response


@app.get("/health")
def health():
    return {"status": "ok", "app": settings.app_name}


app.include_router(auth_router.router)
app.include_router(patients.router)
app.include_router(appointments.router)
app.include_router(pipeline.router)
app.include_router(kpi.router)
app.include_router(services.router)
app.include_router(integrations.router)
app.include_router(financials.router)
app.include_router(staff.router)
app.include_router(inventory.router)
app.include_router(agents.router)
