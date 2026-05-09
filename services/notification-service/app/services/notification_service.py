import logging
from datetime import datetime

from app.core.config import settings
from app.core.haversine import haversine
from app.core.models import IncidentEvent, Notification
from app.repositories.notification_repository import NotificationRepository

logger = logging.getLogger(__name__)


class NotificationService:
    """
    Business logic layer for the Notification Service.

    Responsibilities:
        1. find_nearby_users()  — geofencing via Haversine formula
        2. push_notification()  — write alert to Redis via repository
        3. notify_nearby_users() — orchestrates 1 + 2 for a given event
    """

    def __init__(self, repository: NotificationRepository) -> None:
        self._repo = repository

    async def find_nearby_users(
        self,
        incident_lat: float,
        incident_lng: float,
        radius_metres: float = settings.geofence_radius_metres,
    ) -> list[str]:
        """
        Return the IDs of all users whose cached location is within
        `radius_metres` of the given incident coordinates.

        Steps (as specified in the architecture document):
            1. Read all active user_session:* keys from Redis.
            2. For each user, retrieve their (lat, lng).
            3. Apply Haversine formula.
            4. Return IDs of users within range.
        """
        nearby: list[str] = []

        user_ids = await self._repo.get_all_active_user_ids()
        logger.info("Checking %d active users for proximity", len(user_ids))

        for user_id in user_ids:
            location = await self._repo.get_user_location(user_id)
            if location is None:
                continue  # Location expired or malformed — skip

            user_lat, user_lng = location
            distance = haversine(incident_lat, incident_lng, user_lat, user_lng)

            if distance <= radius_metres:
                nearby.append(user_id)
                logger.debug(
                    "User %s is %.0fm away — within %.0fm radius",
                    user_id,
                    distance,
                    radius_metres,
                )

        logger.info(
            "Found %d users within %.0fm of incident (%.4f, %.4f)",
            len(nearby),
            radius_metres,
            incident_lat,
            incident_lng,
        )
        return nearby

    async def push_notification(self, user_id: str, event: IncidentEvent) -> None:
        """
        Build a Notification object from an IncidentEvent and write it
        to the user's Redis key via the repository.
        """
        notification = Notification(
            incident_id=event.incident_id,
            type=event.type,
            severity=event.severity,
            latitude=event.latitude,
            longitude=event.longitude,
            message=self._build_message(event),
            created_at=datetime.utcnow(),
            is_read=False,
        )
        await self._repo.push_notification(user_id, notification)

    async def notify_nearby_users(self, event: IncidentEvent) -> int:
        """
        Orchestrate the full geofencing + push flow for one IncidentEvent.

        Returns:
            Number of users notified.
        """
        nearby_users = await self.find_nearby_users(event.latitude, event.longitude)

        for user_id in nearby_users:
            await self.push_notification(user_id, event)

        return len(nearby_users)

    # ------------------------------------------------------------------ #
    # Private helpers
    # ------------------------------------------------------------------ #

    @staticmethod
    def _build_message(event: IncidentEvent) -> str:
        severity_label = event.severity.capitalize()
        return (
            f"[{severity_label}] {event.type.replace('_', ' ').title()} reported "
            f"near your location. Stay alert and consider an alternate route."
        )