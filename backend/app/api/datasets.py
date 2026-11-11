import os
import shutil
import json
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, status
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.config import settings
from backend.app.models.dataset import Dataset
from backend.app.schemas.dataset import DatasetOut, DatasetPreview, DatasetMappingUpdate
from backend.app.services.data_loader import DataLoaderService

router = APIRouter(prefix="/datasets", tags=["Datasets"])

@router.post("/upload", response_model=DatasetOut, status_code=status.HTTP_201_CREATED)
async def upload_dataset(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Handles drag-and-drop or file upload for CSV or XLSX files."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename missing.")

    ext = Path(file.filename).suffix.lower()
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported file format. Please upload {', '.join(settings.ALLOWED_EXTENSIONS)}")

    # Save to storage/datasets
    safe_name = f"{Path(file.filename).stem}_{int(os.times().elapsed * 1000)}{ext}"
    dest_path = settings.STORAGE_DATASETS_DIR / safe_name

    with open(dest_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    file_size = dest_path.stat().st_size

    # Inspect structure
    columns, rows = DataLoaderService.load_records(str(dest_path))
    mappings = DataLoaderService.map_columns(columns)

    # Deactivate other datasets
    db.query(Dataset).update({Dataset.is_active: False})

    # Save record
    dataset = Dataset(
        filename=file.filename,
        file_path=str(dest_path),
        row_count=len(rows),
        column_count=len(columns),
        file_size_bytes=file_size,
        is_active=True,
        is_cleaned=False,
        metadata_json=json.dumps({"columns": columns, "mappings": mappings})
    )
    db.add(dataset)
    db.commit()
    db.refresh(dataset)

    return DatasetOut(
        id=dataset.id,
        filename=dataset.filename,
        row_count=dataset.row_count,
        column_count=dataset.column_count,
        file_size_bytes=dataset.file_size_bytes,
        is_active=dataset.is_active,
        is_cleaned=dataset.is_cleaned,
        parent_id=dataset.parent_id,
        uploaded_at=dataset.uploaded_at,
        column_names=columns,
        detected_mappings=mappings
    )

@router.get("", response_model=list[DatasetOut])
def list_datasets(db: Session = Depends(get_db)):
    """Returns all uploaded datasets, with active dataset first."""
    datasets = db.query(Dataset).order_by(Dataset.is_active.desc(), Dataset.uploaded_at.desc()).all()
    results = []
    for d in datasets:
        meta = json.loads(d.metadata_json or "{}")
        results.append(DatasetOut(
            id=d.id,
            filename=d.filename,
            row_count=d.row_count,
            column_count=d.column_count,
            file_size_bytes=d.file_size_bytes,
            is_active=d.is_active,
            is_cleaned=d.is_cleaned,
            parent_id=d.parent_id,
            uploaded_at=d.uploaded_at,
            column_names=meta.get("columns", []),
            detected_mappings=meta.get("mappings", {})
        ))
    return results

@router.get("/{dataset_id}", response_model=DatasetPreview)
def get_dataset_preview(
    dataset_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=200),
    search: Optional[str] = None,
    sort_by: Optional[str] = None,
    sort_order: str = Query("asc", regex="^(asc|desc)$"),
    db: Session = Depends(get_db)
):
    """Returns paginated records and column statistics for Data Explorer."""
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset or not os.path.exists(dataset.file_path):
        raise HTTPException(status_code=404, detail="Dataset not found.")

    columns, rows = DataLoaderService.load_records(dataset.file_path)
    preview = DataLoaderService.get_preview(
        columns, rows, page=page, page_size=page_size,
        search=search, sort_by=sort_by, sort_order=sort_order
    )

    meta = json.loads(dataset.metadata_json or "{}")
    if "mappings" in meta and meta["mappings"]:
        preview["detected_mappings"] = meta["mappings"]

    return DatasetPreview(
        id=dataset.id,
        filename=dataset.filename,
        total_rows=preview["total_rows"],
        total_columns=preview["total_columns"],
        column_info=preview["column_info"],
        missing_values_total=preview["missing_values_total"],
        duplicate_rows_count=preview["duplicate_rows_count"],
        detected_mappings=preview["detected_mappings"],
        sample_rows=preview["sample_rows"],
        page=page,
        page_size=page_size,
        total_pages=preview["total_pages"]
    )

@router.post("/{dataset_id}/select")
def set_active_dataset(dataset_id: int, db: Session = Depends(get_db)):
    """Sets the chosen dataset as active across all modules."""
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found.")

    db.query(Dataset).update({Dataset.is_active: False})
    dataset.is_active = True
    db.commit()
    return {"status": "success", "active_dataset_id": dataset.id, "filename": dataset.filename}

@router.put("/{dataset_id}/mappings")
def update_mappings(dataset_id: int, payload: DatasetMappingUpdate, db: Session = Depends(get_db)):
    """Allows users to manually correct column mappings."""
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found.")

    meta = json.loads(dataset.metadata_json or "{}")
    meta["mappings"] = payload.mappings
    dataset.metadata_json = json.dumps(meta)
    db.commit()
    return {"status": "success", "mappings": payload.mappings}

@router.delete("/{dataset_id}")
def delete_dataset(dataset_id: int, db: Session = Depends(get_db)):
    """Deletes a dataset and removes its file."""
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found.")

    if os.path.exists(dataset.file_path):
        try:
            os.remove(dataset.file_path)
        except OSError:
            pass

    db.delete(dataset)
    db.commit()
    return {"status": "success", "deleted_dataset_id": dataset_id}
