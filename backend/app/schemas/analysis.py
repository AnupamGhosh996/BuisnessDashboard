from typing import Any, Optional
from pydantic import BaseModel

class KPICard(BaseModel):
    id: str
    label: str
    value: float
    formatted_value: str
    change_pct: Optional[float] = None
    subtext: Optional[str] = None
    icon: Optional[str] = None

class OverviewResponse(BaseModel):
    dataset_id: int
    filename: str
    row_count: int
    column_count: int
    kpis: list[KPICard]
    date_range: Optional[dict[str, str]] = None
    categories: list[str] = []
    regions: list[str] = []
    products_count: int = 0
    customers_count: int = 0
    auto_summary: str

class NumericalColumnStats(BaseModel):
    column: str
    count: int
    mean: float
    median: float
    mode: Optional[float] = None
    std: float
    variance: float
    min: float
    max: float
    q25: float
    q75: float
    iqr: float
    skewness: Optional[float] = None

class CategoricalColumnStats(BaseModel):
    column: str
    total_count: int
    unique_count: int
    top_value: Optional[str] = None
    frequencies: list[dict[str, Any]] = []

class StatisticsResponse(BaseModel):
    dataset_id: int
    numerical_stats: list[NumericalColumnStats]
    categorical_stats: list[CategoricalColumnStats]
    auto_eda_narrative: str

class CorrelationMatrix(BaseModel):
    columns: list[str]
    matrix: list[list[float]]

class ChartDataset(BaseModel):
    revenue_over_time: list[dict[str, Any]] = []
    profit_by_category: list[dict[str, Any]] = []
    sales_by_region: list[dict[str, Any]] = []
    product_performance: list[dict[str, Any]] = []
    revenue_contribution: list[dict[str, Any]] = []
    profitability_scatter: list[dict[str, Any]] = []
    monthly_sales_distribution: list[dict[str, Any]] = []

class FilterParams(BaseModel):
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    categories: Optional[list[str]] = None
    regions: Optional[list[str]] = None
    products: Optional[list[str]] = None
