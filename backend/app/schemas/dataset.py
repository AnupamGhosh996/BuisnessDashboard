from typing import Any, Optional
from datetime import datetime
from pydantic import BaseModel

class ColumnInfo(BaseModel):
    name: str
    data_type: str
    missing_count: int
    unique_count: int
    sample_values: list[Any] = []
    role_mapping: Optional[str] = None

class DatasetOut(BaseModel):
    id: int
    filename: str
    row_count: int
    column_count: int
    file_size_bytes: int
    is_active: bool
    is_cleaned: bool
    parent_id: Optional[int] = None
    uploaded_at: datetime
    column_names: list[str] = []
    detected_mappings: dict[str, str] = {}

    class Config:
        from_attributes = True

class DatasetPreview(BaseModel):
    id: int
    filename: str
    total_rows: int
    total_columns: int
    column_info: list[ColumnInfo]
    missing_values_total: int
    duplicate_rows_count: int
    detected_mappings: dict[str, str]
    sample_rows: list[dict[str, Any]]
    page: int = 1
    page_size: int = 25
    total_pages: int = 1

class DatasetMappingUpdate(BaseModel):
    mappings: dict[str, str]
