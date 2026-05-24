import logging
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Tracks all active WebSocket connections, keyed by user_id.

    When the notification worker pushes a notification it calls
    send_to_user() — if that user has an open WebSocket connection
    the notification is delivered instantly. If they are offline,
    nothing happens (the notification is still in Redis for polling).

    One user can have multiple connections (e.g. two browser tabs)
    so we store a list of WebSockets per user_id.
    """

    def __init__(self) -> None:
        # { user_id: [WebSocket, ...] }
        self._active: dict[str, list[WebSocket]] = {}

    async def connect(self, user_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        self._active.setdefault(user_id, []).append(websocket)
        logger.info("WebSocket connected for user %s (%d total connections)",
                    user_id, len(self._active[user_id]))

    def disconnect(self, user_id: str, websocket: WebSocket) -> None:
        connections = self._active.get(user_id, [])
        if websocket in connections:
            connections.remove(websocket)
        if not connections:
            self._active.pop(user_id, None)
        logger.info("WebSocket disconnected for user %s", user_id)

    async def send_to_user(self, user_id: str, message: dict) -> None:
        """
        Push a JSON message to all open connections for this user.
        Silently removes any broken connections.
        """
        connections = self._active.get(user_id, [])
        broken = []

        for websocket in connections:
            try:
                await websocket.send_json(message)
            except Exception:
                logger.warning("Broken WebSocket for user %s — removing", user_id)
                broken.append(websocket)

        for websocket in broken:
            self.disconnect(user_id, websocket)

    async def broadcast(self, message: dict) -> None:
        """
        Push a JSON message to ALL connected users.
        Used for events that affect every client — e.g. incident resolved.
        """
        for user_id in list(self._active.keys()):
            await self.send_to_user(user_id, message)

    def is_connected(self, user_id: str) -> bool:
        return bool(self._active.get(user_id))


# Single shared instance — imported by routes.py and notification_service.py
manager = ConnectionManager()