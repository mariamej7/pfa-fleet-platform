
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.vehicles import router as vehicles_router
from app.api.alerts import router as alerts_router
from app.api.dashboard import router as dashboard_router
from app.api.fuel import router as fuel_router
from app.api.analytics import router as analytics_router
from app.api.data_quality import router as data_quality_router
from app.api.imports import router as imports_router


app = FastAPI(
    title="PFA Fleet Platform API",
    description=(
        "API de la plateforme d'analyse de flotte "
        "et de détection d'anomalies carburant"
    ),
    version="1.0.0"
)


# Autoriser le frontend local et le futur site de demonstration
allowed_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

# Cette variable sera configuree lors du deploiement.
frontend_url = os.getenv("FRONTEND_URL", "").strip().rstrip("/")

if frontend_url:
    allowed_origins.append(frontend_url)


app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {
        "message": "PFA Fleet Platform API"
    }


@app.get("/health")
def health():
    return {
        "status": "ok"
    }


app.include_router(vehicles_router)
app.include_router(alerts_router)
app.include_router(dashboard_router)
app.include_router(fuel_router)
app.include_router(analytics_router)
app.include_router(data_quality_router)
app.include_router(imports_router)