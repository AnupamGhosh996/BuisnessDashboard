import os
import json
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models.dataset import Dataset
from backend.app.schemas.analysis import OverviewResponse, StatisticsResponse, CorrelationMatrix, ChartDataset
from backend.app.services.data_loader import DataLoaderService
from backend.app.services.eda_engine import EDAEngineService
from backend.app.services.analytics_engine import AnalyticsEngineService

router = APIRouter(prefix="/analysis", tags=["Data Analysis & Dashboard"])

def get_dataset_records(dataset_id: int, db: Session):
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset or not os.path.exists(dataset.file_path):
        raise HTTPException(status_code=404, detail="Dataset not found.")
    columns, rows = DataLoaderService.load_records(dataset.file_path)
    meta = json.loads(dataset.metadata_json or "{}")
    custom_mappings = meta.get("mappings")
    return dataset, columns, rows, custom_mappings

@router.get("/{dataset_id}/overview", response_model=OverviewResponse)
def get_overview(
    dataset_id: int,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    category: Optional[list[str]] = Query(None),
    region: Optional[list[str]] = Query(None),
    product: Optional[list[str]] = Query(None),
    db: Session = Depends(get_db)
):
    """Returns dynamic KPI cards and overview metadata with filter support."""
    dataset, columns, rows, custom_mappings = get_dataset_records(dataset_id, db)
    filter_params = {
        "start_date": start_date,
        "end_date": end_date,
        "categories": category,
        "regions": region,
        "products": product
    }

    overview = AnalyticsEngineService.calculate_overview(
        columns, rows, custom_mappings=custom_mappings, filter_params=filter_params
    )

    return OverviewResponse(
        dataset_id=dataset.id,
        filename=dataset.filename,
        row_count=overview["row_count"],
        column_count=overview["column_count"],
        kpis=overview["kpis"],
        date_range=overview["date_range"],
        categories=overview["categories"],
        regions=overview["regions"],
        products_count=overview["products_count"],
        customers_count=overview["customers_count"],
        auto_summary=overview["auto_summary"]
    )

@router.get("/{dataset_id}/statistics", response_model=StatisticsResponse)
def get_statistics(dataset_id: int, db: Session = Depends(get_db)):
    """Computes automated EDA numerical & categorical statistics and insights."""
    dataset, columns, rows, _ = get_dataset_records(dataset_id, db)
    eda = EDAEngineService.calculate_eda(columns, rows)

    return StatisticsResponse(
        dataset_id=dataset.id,
        numerical_stats=eda["numerical_stats"],
        categorical_stats=eda["categorical_stats"],
        auto_eda_narrative=eda["auto_summary"]
    )

@router.get("/{dataset_id}/correlations", response_model=CorrelationMatrix)
def get_correlations(dataset_id: int, db: Session = Depends(get_db)):
    """Computes Pearson correlation matrix between all numerical columns."""
    _, columns, rows, _ = get_dataset_records(dataset_id, db)
    eda = EDAEngineService.calculate_eda(columns, rows)
    return CorrelationMatrix(
        columns=eda["correlation_matrix"]["columns"],
        matrix=eda["correlation_matrix"]["matrix"]
    )

@router.get("/{dataset_id}/charts", response_model=ChartDataset)
def get_charts(
    dataset_id: int,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    category: Optional[list[str]] = Query(None),
    region: Optional[list[str]] = Query(None),
    product: Optional[list[str]] = Query(None),
    db: Session = Depends(get_db)
):
    """Generates all 7 interactive charts based on active filters."""
    _, columns, rows, custom_mappings = get_dataset_records(dataset_id, db)
    filter_params = {
        "start_date": start_date,
        "end_date": end_date,
        "categories": category,
        "regions": region,
        "products": product
    }

    charts = AnalyticsEngineService.generate_charts(
        columns, rows, custom_mappings=custom_mappings, filter_params=filter_params
    )

    return ChartDataset(
        revenue_over_time=charts["revenue_over_time"],
        profit_by_category=charts["profit_by_category"],
        sales_by_region=charts["sales_by_region"],
        product_performance=charts["product_performance"],
        revenue_contribution=charts["revenue_contribution"],
        profitability_scatter=charts["profitability_scatter"],
        monthly_sales_distribution=charts["monthly_sales_distribution"]
    )
