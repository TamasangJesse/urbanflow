import logging
from datetime import datetime, timezone
from typing import Optional

from bson import ObjectId

from app.database import get_database

logger = logging.getLogger(__name__)


class ChatRepository:
    def _collection(self):
        db = get_database()
        return db["chat_history"]

    async def save_chat(
        self,
        user_id: str,
        question: str,
        answer: str,
        location_detected: Optional[str],
        context_used: dict,
    ) -> str:
        doc = {
            "user_id": user_id,
            "question": question,
            "answer": answer,
            "location_detected": location_detected,
            "context_used": context_used,
            "created_at": datetime.now(timezone.utc),
        }
        result = await self._collection().insert_one(doc)
        return str(result.inserted_id)

    async def get_history(self, user_id: str, limit: int = 20) -> list:
        cursor = (
            self._collection()
            .find({"user_id": user_id})
            .sort("created_at", -1)
            .limit(limit)
        )
        items = []
        async for doc in cursor:
            items.append(
                {
                    "id": str(doc["_id"]),
                    "question": doc.get("question", ""),
                    "answer": doc.get("answer", ""),
                    "location_detected": doc.get("location_detected"),
                    "created_at": doc.get("created_at"),
                }
            )
        return items

    async def delete_history(self, user_id: str) -> int:
        result = await self._collection().delete_many({"user_id": user_id})
        return result.deleted_count