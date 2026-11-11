from typing import Optional, Any
from pydantic import BaseModel

class AnomalyItem(BaseModel):
    record_index: int
    record_id: Optional[str] = None
    date: Optional[str] = None
    metric: str
    actual_value: float
    expected_baseline: float
    expected_lower: float
    expected_upper: float
    deviation_pct: float
    severity: str  # "Low", "Medium", "High", "Critical"
    reason: str
    is_confirmed_issue: bool = False

class AnomalyDetectRequest(BaseModel):
    method: str = "isolation_forest"  # "isolation_forest", "zscore", "iqr"
    metric_column: Optional[str] = None
    contamination_pct: float = 0.05

class AnomalyDetectResponse(BaseModel):
    dataset_id: int
    metric_analyzed: str
    method_used: str
    total_records: int
    anomalies_detected_count: int
    anomaly_rate_pct: float
    anomalies: list[AnomalyItem]
    time_series_plot: list[dict[str, Any]] = []
