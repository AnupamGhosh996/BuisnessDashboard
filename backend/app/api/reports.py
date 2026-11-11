import os
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models.dataset import Dataset
from backend.app.models.report import Report
from backend.app.schemas.report import ReportGenerateRequest, ReportOut
from backend.app.services.data_loader import DataLoaderService
from backend.app.services.report_generator import ReportGeneratorService

router = APIRouter(prefix="/reports", tags=["Reports"])

@router.post("/generate", response_model=ReportOut)
def generate_report(payload: ReportGenerateRequest, db: Session = Depends(get_db)):
    """Generates an executive analytical report and exports to PDF, Excel, or CSV."""
    dataset = db.query(Dataset).filter(Dataset.id == payload.dataset_id).first()
    if not dataset or not os.path.exists(dataset.file_path):
        raise HTTPException(status_code=404, detail="Dataset not found.")

    columns, rows = DataLoaderService.load_records(dataset.file_path)

    # Generate full report content
    content = ReportGeneratorService.generate_report_content(
        columns=columns,
        rows=rows,
        dataset_name=dataset.filename,
        report_type=payload.report_type,
        custom_title=payload.title
    )

    # Save to disk in requested format
    file_path = ReportGeneratorService.export_report_file(
        report_content=content,
        report_format=payload.format
    )

    # Register in database
    report = Report(
        dataset_id=dataset.id,
        report_type=payload.report_type,
        title=content["title"],
        file_path=file_path,
        file_format=payload.format,
        summary_text=content["executive_summary"]
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    return ReportOut(
        id=report.id,
        dataset_id=report.dataset_id,
        title=report.title,
        report_type=report.report_type,
        file_format=report.file_format,
        created_at=report.created_at,
        download_url=f"/api/reports/{report.id}/download",
        summary_text=report.summary_text
    )

@router.get("", response_model=list[ReportOut])
def list_reports(db: Session = Depends(get_db)):
    """Returns all generated reports."""
    reports = db.query(Report).order_by(Report.created_at.desc()).all()
    return [
        ReportOut(
            id=r.id,
            dataset_id=r.dataset_id,
            title=r.title,
            report_type=r.report_type,
            file_format=r.file_format,
            created_at=r.created_at,
            download_url=f"/api/reports/{r.id}/download",
            summary_text=r.summary_text
        )
        for r in reports
    ]

@router.get("/{report_id}/download")
def download_report(report_id: int, db: Session = Depends(get_db)):
    """Serves generated report file for direct browser download."""
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report or not os.path.exists(report.file_path):
        raise HTTPException(status_code=404, detail="Report file not found.")

    media_types = {
        "pdf": "application/pdf",
        "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "csv": "text/csv",
        "html": "text/html"
    }
    media_type = media_types.get(report.file_format, "application/octet-stream")
    filename = os.path.basename(report.file_path)

    return FileResponse(
        path=report.file_path,
        media_type=media_type,
        filename=filename
    )
