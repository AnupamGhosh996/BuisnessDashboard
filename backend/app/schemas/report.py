from typing import Optional, Any
from datetime import datetime
from pydantic import BaseModel

class ReportGenerateRequest(BaseModel):
    dataset_id: int
    report_type: str = "executive_summary"  # "daily", "weekly", "monthly", "revenue", "profitability", "executive_summary"
    title: Optional[str] = None
    format: str = "pdf"  # "pdf", "xlsx", "csv"

class ReportOut(BaseModel):
    id: int
    dataset_id: int
    title: str
    report_type: str
    file_format: str
    created_at: datetime
    download_url: str
    summary_text: Optional[str] = None

    class Config:
        from_attributes = True

class ReportContentPreview(BaseModel):
    title: str
    report_type: str
    dataset_name: str
    generated_at: str
    executive_summary: str
    kpis: list[dict[str, Any]]
    trends: list[str]
    category_analysis: list[dict[str, Any]]
    regional_analysis: list[dict[str, Any]]
    anomalies_summary: list[str]
    forecast_summary: str
    strategic_recommendations: list[str]
