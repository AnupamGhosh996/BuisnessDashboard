import os
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models.dataset import Dataset
from backend.app.schemas.forecast import ForecastRequest, ForecastResponse
from backend.app.services.data_loader import DataLoaderService
from backend.app.services.forecasting import ForecastingService

router = APIRouter(prefix="/forecast", tags=["Business Forecasting"])

@router.post("/{dataset_id}", response_model=ForecastResponse)
def forecast_performance(dataset_id: int, payload: ForecastRequest, db: Session = Depends(get_db)):
    """Computes future business metric forecast with confidence bounds and accuracy metrics."""
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset or not os.path.exists(dataset.file_path):
        raise HTTPException(status_code=404, detail="Dataset not found.")

    columns, rows = DataLoaderService.load_records(dataset.file_path)

    try:
        forecast_result = ForecastingService.generate_forecast(
            columns=columns,
            rows=rows,
            metric_column=payload.metric_column,
            date_column=payload.date_column,
            horizon_days=payload.horizon_days,
            method=payload.method
        )
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Forecasting calculation failed: {str(e)}")

    forecast_result["dataset_id"] = dataset.id
    return ForecastResponse(**forecast_result)
