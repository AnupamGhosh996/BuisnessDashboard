from typing import Optional, Any
from pydantic import BaseModel

class CleaningIssue(BaseModel):
    issue_type: str
    column: Optional[str] = None
    affected_count: int
    description: str
    suggested_action: str

class CleaningPreviewResponse(BaseModel):
    dataset_id: int
    filename: str
    total_rows: int
    duplicate_rows: int
    missing_values_by_column: dict[str, int]
    outliers_by_column: dict[str, int]
    issues: list[CleaningIssue]
    cleaning_suggestions: list[str]

class CleaningApplyRequest(BaseModel):
    remove_duplicates: bool = True
    fill_numerical: Optional[str] = "mean"  # "mean", "median", "none"
    fill_categorical: Optional[str] = "mode"  # "mode", "none"
    drop_missing_rows: bool = False
    convert_date_columns: list[str] = []
    normalize_columns: list[str] = []

class CleaningApplyResponse(BaseModel):
    original_dataset_id: int
    cleaned_dataset_id: int
    filename: str
    rows_before: int
    rows_after: int
    duplicates_removed: int
    missing_imputed_count: int
    summary_notes: list[str]
