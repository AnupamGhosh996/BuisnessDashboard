import os
import csv
import json
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.config import settings
from backend.app.models.dataset import Dataset
from backend.app.schemas.cleaning import CleaningPreviewResponse, CleaningApplyRequest, CleaningApplyResponse
from backend.app.services.data_loader import DataLoaderService
from backend.app.services.data_cleaner import DataCleanerService

router = APIRouter(prefix="/cleaning", tags=["Data Cleaning"])

@router.post("/{dataset_id}/preview", response_model=CleaningPreviewResponse)
def preview_cleaning(dataset_id: int, db: Session = Depends(get_db)):
    """Scans dataset for duplicates, missing values, outliers, and gives suggestions."""
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset or not os.path.exists(dataset.file_path):
        raise HTTPException(status_code=404, detail="Dataset not found.")

    columns, rows = DataLoaderService.load_records(dataset.file_path)
    issues_report = DataCleanerService.inspect_dataset(columns, rows)

    return CleaningPreviewResponse(
        dataset_id=dataset.id,
        filename=dataset.filename,
        total_rows=issues_report["total_rows"],
        duplicate_rows=issues_report["duplicate_rows"],
        missing_values_by_column=issues_report["missing_values_by_column"],
        outliers_by_column=issues_report["outliers_by_column"],
        issues=issues_report["issues"],
        cleaning_suggestions=issues_report["cleaning_suggestions"]
    )

@router.post("/{dataset_id}/apply", response_model=CleaningApplyResponse)
def apply_cleaning(dataset_id: int, payload: CleaningApplyRequest, db: Session = Depends(get_db)):
    """
    Creates a NEW cleaned copy of the dataset. Never modifies the original uploaded file directly!
    """
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset or not os.path.exists(dataset.file_path):
        raise HTTPException(status_code=404, detail="Dataset not found.")

    columns, rows = DataLoaderService.load_records(dataset.file_path)

    cleaned_rows, summary = DataCleanerService.apply_cleaning(
        columns=columns,
        rows=rows,
        remove_duplicates=payload.remove_duplicates,
        fill_numerical=payload.fill_numerical,
        fill_categorical=payload.fill_categorical,
        drop_missing_rows=payload.drop_missing_rows,
        normalize_columns=payload.normalize_columns
    )

    # Determine final column names if normalized columns were appended
    final_columns = list(cleaned_rows[0].keys()) if cleaned_rows else columns

    # Save cleaned file to storage
    orig_name = Path(dataset.filename).stem
    cleaned_filename = f"{orig_name}_cleaned.csv"
    dest_path = settings.STORAGE_DATASETS_DIR / f"{orig_name}_cleaned_{int(os.times().elapsed * 1000)}.csv"

    with open(dest_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=final_columns)
        writer.writeheader()
        writer.writerows(cleaned_rows)

    file_size = dest_path.stat().st_size
    new_mappings = DataLoaderService.map_columns(final_columns)

    # Deactivate other datasets and make the cleaned dataset active
    db.query(Dataset).update({Dataset.is_active: False})

    cleaned_dataset = Dataset(
        filename=cleaned_filename,
        file_path=str(dest_path),
        row_count=len(cleaned_rows),
        column_count=len(final_columns),
        file_size_bytes=file_size,
        is_active=True,
        is_cleaned=True,
        parent_id=dataset.id,
        metadata_json=json.dumps({"columns": final_columns, "mappings": new_mappings})
    )
    db.add(cleaned_dataset)
    db.commit()
    db.refresh(cleaned_dataset)

    return CleaningApplyResponse(
        original_dataset_id=dataset.id,
        cleaned_dataset_id=cleaned_dataset.id,
        filename=cleaned_filename,
        rows_before=summary["rows_before"],
        rows_after=summary["rows_after"],
        duplicates_removed=summary["duplicates_removed"],
        missing_imputed_count=summary["missing_imputed_count"],
        summary_notes=summary["summary_notes"]
    )
