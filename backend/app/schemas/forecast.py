from typing import Optional
from pydantic import BaseModel

class ForecastPoint(BaseModel):
    date: str
    historical_value: Optional[float] = None
    forecast_value: Optional[float] = None
    lower_bound: Optional[float] = None
    upper_bound: Optional[float] = None

class ForecastAccuracy(BaseModel):
    mae: float
    rmse: float
    mape: float

class ForecastRequest(BaseModel):
    metric_column: Optional[str] = None
    date_column: Optional[str] = None
    horizon_days: int = 30  # 7, 30, 90, 180
    method: str = "linear"  # "linear", "moving_average", "exponential_smoothing"

class ForecastResponse(BaseModel):
    dataset_id: int
    metric: str
    date_column: str
    horizon_days: int
    method: str
    trend_direction: str  # "Upward Growth", "Downward Trend", "Stable"
    accuracy: ForecastAccuracy
    points: list[ForecastPoint]
    historical_count: int
    forecast_count: int
    disclaimer: str = "Forecasts are algorithmic estimates based on historical trajectories and should be evaluated alongside market domain conditions."
