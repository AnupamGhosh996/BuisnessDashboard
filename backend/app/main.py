import os
import json
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.app.config import settings
from backend.app.database import engine, Base, SessionLocal
from backend.app.models.dataset import Dataset
from backend.app.models.user import User
from backend.app.models.conversation import Conversation, Message
from backend.app.models.report import Report
from backend.app.services.data_loader import DataLoaderService

from backend.app.api.datasets import router as datasets_router
from backend.app.api.cleaning import router as cleaning_router
from backend.app.api.analysis import router as analysis_router
from backend.app.api.ai import router as ai_router
from backend.app.api.anomaly import router as anomaly_router
from backend.app.api.forecast import router as forecast_router
from backend.app.api.reports import router as reports_router
from backend.app.api.health import router as health_router

# Lifespan startup/shutdown handler
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create DB tables
    Base.metadata.create_all(bind=engine)

    # Auto-seed default sample dataset if database has no datasets
    db = SessionLocal()
    try:
        count = db.query(Dataset).count()
        if count == 0:
            sample_csv = settings.STORAGE_DATASETS_DIR / "sample_sales_dataset.csv"
            if sample_csv.exists():
                cols, rows = DataLoaderService.load_records(str(sample_csv))
                mappings = DataLoaderService.map_columns(cols)
                sample_ds = Dataset(
                    filename="sample_sales_dataset.csv",
                    file_path=str(sample_csv),
                    row_count=len(rows),
                    column_count=len(cols),
                    file_size_bytes=sample_csv.stat().st_size,
                    is_active=True,
                    is_cleaned=False,
                    metadata_json=json.dumps({"columns": cols, "mappings": mappings})
                )
                db.add(sample_ds)
                db.commit()
                print(f"[InsightIQ] Auto-seeded active sample dataset with {len(rows)} records.")
    except Exception as e:
        print(f"[InsightIQ] Startup seeding notice: {e}")
    finally:
        db.close()

    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="InsightIQ – AI-Powered Enterprise Business Intelligence Platform",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(datasets_router, prefix=settings.API_V1_STR)
app.include_router(cleaning_router, prefix=settings.API_V1_STR)
app.include_router(analysis_router, prefix=settings.API_V1_STR)
app.include_router(ai_router, prefix=settings.API_V1_STR)
app.include_router(anomaly_router, prefix=settings.API_V1_STR)
app.include_router(forecast_router, prefix=settings.API_V1_STR)
app.include_router(reports_router, prefix=settings.API_V1_STR)
app.include_router(health_router, prefix=settings.API_V1_STR)

# Serve Frontend static build if built in frontend/dist
frontend_dist = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")
