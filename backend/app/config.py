import os
from pathlib import Path

try:
    from pydantic import BaseModel
    class BaseConfig(BaseModel):
        pass
except ImportError:
    class BaseConfig:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)

BASE_DIR = Path(__file__).resolve().parent.parent.parent

class Settings(BaseConfig):
    PROJECT_NAME: str = "InsightIQ"
    API_V1_STR: str = "/api"
    
    # Storage paths
    STORAGE_DATASETS_DIR: Path = BASE_DIR / "storage" / "datasets"
    STORAGE_REPORTS_DIR: Path = BASE_DIR / "storage" / "reports"
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'insightiq.db'}")
    
    # Anthropic Claude API
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    ANTHROPIC_MODEL: str = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")
    
    # Security & limits
    MAX_FILE_SIZE_MB: int = int(os.getenv("MAX_FILE_SIZE_MB", "50"))
    ALLOWED_EXTENSIONS: list = [".csv", ".xlsx", ".xls"]
    
    # CORS
    ALLOWED_ORIGINS: list = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "*"
    ]

settings = Settings()

# Ensure storage directories exist
settings.STORAGE_DATASETS_DIR.mkdir(parents=True, exist_ok=True)
settings.STORAGE_REPORTS_DIR.mkdir(parents=True, exist_ok=True)

