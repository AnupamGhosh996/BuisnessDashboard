import os
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models.dataset import Dataset
from backend.app.schemas.anomaly import AnomalyDetectRequest, AnomalyDetectResponse
from backend.app.services.data_loader import DataLoaderService
from backend.app.services.anomaly_detector import AnomalyDetectorService

router = APIRouter(prefix="/anomaly", tags=["Anomaly Detection"])

@router.post("/{dataset_id}/detect", response_model=AnomalyDetectResponse)
def detect_anomalies(dataset_id: int, payload: AnomalyDetectRequest, db: Session = Depends(get_db)):
    """Runs statistical/machine-learning anomaly detection on the selected dataset."""
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset or not os.path.exists(dataset.file_path):
        raise HTTPException(status_code=404, detail="Dataset not found.")

    columns, rows = DataLoaderService.load_records(dataset.file_path)

    result = AnomalyDetectorService.detect_anomalies(
        columns=columns,
        rows=rows,
        method=payload.method,
        metric_column=payload.metric_column,
        contamination_pct=payload.contamination_pct
    )

    result["dataset_id"] = dataset.id
    return AnomalyDetectResponse(**result)
