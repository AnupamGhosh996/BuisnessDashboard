import os
import sys
from fastapi import APIRouter
from backend.app.config import settings

router = APIRouter(tags=["System"])

@router.get("/health")
def health_check():
    """System health check endpoint."""
    has_anthropic = bool(os.getenv("ANTHROPIC_API_KEY", settings.ANTHROPIC_API_KEY))
    return {
        "status": "healthy",
        "app_name": settings.PROJECT_NAME,
        "python_version": sys.version.split()[0],
        "database": "connected",
        "ai_status": "ready" if has_anthropic else "deterministic_fallback (set ANTHROPIC_API_KEY for live Claude)",
        "datasets_storage": str(settings.STORAGE_DATASETS_DIR),
        "reports_storage": str(settings.STORAGE_REPORTS_DIR)
    }
