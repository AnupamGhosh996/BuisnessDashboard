from typing import Any, Optional
from pydantic import BaseModel

class AIChatRequest(BaseModel):
    dataset_id: int
    message: str
    conversation_id: Optional[int] = None

class ChartRecommendation(BaseModel):
    recommended: bool
    chart_type: str  # "line", "bar", "pie", "scatter", "none"
    title: str
    x_key: str
    y_key: str
    data: list[dict[str, Any]] = []

class AIChatResponse(BaseModel):
    conversation_id: int
    message_id: int
    answer: str
    query_plan: dict[str, Any]
    verified_metrics: dict[str, Any]
    chart_recommendation: Optional[ChartRecommendation] = None
    suggested_follow_ups: list[str] = []
    is_live_ai: bool = False

class SuggestedQuestionsResponse(BaseModel):
    dataset_id: int
    suggestions: list[str]
