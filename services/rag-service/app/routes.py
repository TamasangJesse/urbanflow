import logging
from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth import get_current_user
from app.models import ChatHistoryItem, ChatRequest, ChatResponse
from app.rag_engine import generate_answer
from app.repository import ChatRepository

logger = logging.getLogger(__name__)

router = APIRouter()
repo = ChatRepository()


# ─── Health Check ─────────────────────────────────────────────────────────────

@router.get("/health")
async def health_check():
    return {"status": "ok", "service": "rag-service"}


# ─── COMMAND: POST /chat ───────────────────────────────────────────────────────

@router.post("/chat", response_model=ChatResponse)
async def chat(
    body: ChatRequest,
    current_user: dict = Depends(get_current_user),
):
    user_id = current_user["user_id"]
    token = current_user["token"]

    result = await generate_answer(
        question=body.question,
        latitude=body.latitude,
        longitude=body.longitude,
        token=token,
    )

    created_at = datetime.now(timezone.utc)

    try:
        await repo.save_chat(
            user_id=user_id,
            question=body.question,
            answer=result["answer"],
            location_detected=result["location_detected"],
            context_used=result["context_used"],
        )
    except Exception as exc:
        logger.error("Failed to save chat to MongoDB: %s", exc)

    return ChatResponse(
        answer=result["answer"],
        question=body.question,
        location_detected=result["location_detected"],
        created_at=created_at,
    )


# ─── QUERY: GET /chat/history/{user_id} ───────────────────────────────────────

@router.get("/chat/history/{user_id}", response_model=List[ChatHistoryItem])
async def get_history(
    user_id: str,
    current_user: dict = Depends(get_current_user),
):
    if current_user["user_id"] != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only access your own chat history",
        )
    items = await repo.get_history(user_id)
    return [ChatHistoryItem(**item) for item in items]


# ─── COMMAND: DELETE /chat/history/{user_id} ──────────────────────────────────

@router.delete("/chat/history/{user_id}")
async def delete_history(
    user_id: str,
    current_user: dict = Depends(get_current_user),
):
    if current_user["user_id"] != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own chat history",
        )
    count = await repo.delete_history(user_id)
    return {"deleted": count, "message": "History cleared"}