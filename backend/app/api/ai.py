import os
import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models.dataset import Dataset
from backend.app.models.conversation import Conversation, Message
from backend.app.schemas.ai import AIChatRequest, AIChatResponse, SuggestedQuestionsResponse
from backend.app.services.data_loader import DataLoaderService
from backend.app.services.ai_analyst import AIAnalystService

router = APIRouter(prefix="/ai", tags=["AI Data Analyst"])

@router.post("/chat", response_model=AIChatResponse)
def chat_with_analyst(payload: AIChatRequest, db: Session = Depends(get_db)):
    """
    Submits user question, performs safe allowlisted numerical calculations,
    and returns mathematically grounded AI insights with recommended charts.
    """
    dataset = db.query(Dataset).filter(Dataset.id == payload.dataset_id).first()
    if not dataset or not os.path.exists(dataset.file_path):
        raise HTTPException(status_code=404, detail="Active dataset not found.")

    columns, rows = DataLoaderService.load_records(dataset.file_path)

    # Manage Conversation
    conversation = None
    if payload.conversation_id:
        conversation = db.query(Conversation).filter(Conversation.id == payload.conversation_id).first()

    if not conversation:
        conversation = Conversation(
            dataset_id=dataset.id,
            title=f"Chat: {payload.message[:35]}..."
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)

    # Save User message
    user_msg = Message(
        conversation_id=conversation.id,
        role="user",
        content=payload.message
    )
    db.add(user_msg)
    db.commit()

    # Load history
    history_msgs = (
        db.query(Message)
        .filter(Message.conversation_id == conversation.id)
        .order_by(Message.created_at.asc())
        .all()
    )
    conv_hist = [{"role": m.role, "content": m.content} for m in history_msgs]

    # Generate verified computation & explanation
    ai_result = AIAnalystService.generate_response(
        query=payload.message,
        columns=columns,
        rows=rows,
        conversation_history=conv_hist
    )

    # Save Assistant message
    assistant_msg = Message(
        conversation_id=conversation.id,
        role="assistant",
        content=ai_result["answer"],
        query_plan_json=json.dumps(ai_result["query_plan"]),
        chart_recommendation_json=json.dumps(ai_result["chart_recommendation"]) if ai_result["chart_recommendation"] else None,
        metrics_context_json=json.dumps(ai_result["verified_metrics"])
    )
    db.add(assistant_msg)
    db.commit()
    db.refresh(assistant_msg)

    return AIChatResponse(
        conversation_id=conversation.id,
        message_id=assistant_msg.id,
        answer=ai_result["answer"],
        query_plan=ai_result["query_plan"],
        verified_metrics=ai_result["verified_metrics"],
        chart_recommendation=ai_result["chart_recommendation"],
        suggested_follow_ups=ai_result["suggested_follow_ups"],
        is_live_ai=ai_result["is_live_ai"]
    )

@router.get("/history/{conversation_id}")
def get_chat_history(conversation_id: int, db: Session = Depends(get_db)):
    """Returns conversation message thread with verified metrics and charts."""
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found.")

    messages = (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc())
        .all()
    )

    result = []
    for m in messages:
        result.append({
            "id": m.id,
            "role": m.role,
            "content": m.content,
            "query_plan": json.loads(m.query_plan_json) if m.query_plan_json else None,
            "chart_recommendation": json.loads(m.chart_recommendation_json) if m.chart_recommendation_json else None,
            "verified_metrics": json.loads(m.metrics_context_json) if m.metrics_context_json else None,
            "created_at": m.created_at
        })

    return {"conversation_id": conv.id, "title": conv.title, "messages": result}

@router.get("/suggestions/{dataset_id}", response_model=SuggestedQuestionsResponse)
def get_suggestions(dataset_id: int, db: Session = Depends(get_db)):
    """Provides relevant business questions tailored to this dataset's columns."""
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset or not os.path.exists(dataset.file_path):
        raise HTTPException(status_code=404, detail="Dataset not found.")

    columns, _ = DataLoaderService.load_records(dataset.file_path)
    suggestions = AIAnalystService.get_suggested_questions(columns)
    return SuggestedQuestionsResponse(dataset_id=dataset_id, suggestions=suggestions)
