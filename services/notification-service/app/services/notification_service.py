import logging
from datetime import datetime

from app.core.config import settings
from app.core.connection_manager import manager
from app.core.haversine import haversine
from app.core.models import IncidentEvent, Notification
from app.repositories.notification_repository import NotificationRepository

logger = logging.getLogger(__name__)

# How close an incident must be to any point on the user's route to trigger
# a notification. 300m matches the frontend's checkRoute threshold.
_ROUTE_INCIDENT_THRESHOLD_METRES = 300.0


class NotificationService:
    """
    Business logic layer for the Notification Service.

    Notification is triggered in TWO ways:
        1. Route-based  — incident is within 300m of any point on the
                          user's active planned route (most important)
        2. Proximity    — user is within 5km of the incident and has
                          no active route (fallback)
    """

    def __init__(self, repository: NotificationRepository) -> None:
        self._repo = repository

    async def find_nearby_users(
        self,
        incident_lat: float,
        incident_lng: float,
        radius_metres: float = settings.geofence_radius_metres,
        exclude_user_id: str | None = None,
    ) -> list[str]:
        """
        Return the IDs of all users who should be notified about this incident.

        For each active user:
            1. If they have an active route — check if the incident is within
               300m of any point on that route. If yes, notify them.
            2. If they have no active route — fall back to the original
               Haversine 5km proximity check.

        The reporter of the incident is always excluded.
        """
        nearby: list[str] = []

        user_ids = await self._repo.get_all_active_user_ids()
        logger.info("Checking %d active users for proximity", len(user_ids))

        for user_id in user_ids:
            if user_id == exclude_user_id:
                continue

            location = await self._repo.get_user_location(user_id)
            if location is None:
                continue

            # Try route-based check first
            route_points = await self._repo.get_user_route_points(user_id)

            if route_points:
                if self._incident_on_route(incident_lat, incident_lng, route_points):
                    nearby.append(user_id)
                    logger.info(
                        "User %s notified — incident is on their active route", user_id
                    )
            else:
                # No active route — fall back to proximity check
                user_lat, user_lng = location
                distance = haversine(incident_lat, incident_lng, user_lat, user_lng)
                if distance <= radius_metres:
                    nearby.append(user_id)
                    logger.info(
                        "User %s notified — %.0fm from incident (proximity fallback)",
                        user_id,
                        distance,
                    )

        logger.info(
            "Found %d users to notify for incident at (%.4f, %.4f)",
            len(nearby),
            incident_lat,
            incident_lng,
        )
        return nearby

    async def push_notification(self, user_id: str, event: IncidentEvent) -> None:
        """
        Build a Notification object from an IncidentEvent:
            1. Write it to Redis (persists for polling / history)
            2. Push it instantly via WebSocket if the user is connected
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

        # Always write to Redis — user may be offline and poll later
        await self._repo.push_notification(user_id, notification)

        # If user has an open WebSocket connection, push instantly
        if manager.is_connected(user_id):
            await manager.send_to_user(
                user_id,
                notification.model_dump(mode="json"),
            )
            logger.info("WebSocket push sent to user %s", user_id)

    async def notify_nearby_users(self, event: IncidentEvent) -> int:
        """
        Orchestrate the full geofencing + push flow for one IncidentEvent.

        Returns:
            Number of users notified.
        """
        nearby_users = await self.find_nearby_users(
            event.latitude,
            event.longitude,
            exclude_user_id=event.reported_by,
        )

        for user_id in nearby_users:
            await self.push_notification(user_id, event)

        return len(nearby_users)

    # ------------------------------------------------------------------ #
    # Private helpers
    # ------------------------------------------------------------------ #

    @staticmethod
    def _incident_on_route(
        incident_lat: float,
        incident_lng: float,
        route_points: list[tuple[float, float]],
    ) -> bool:
        """
        Return True if the incident is within 300m of any point on the route.

        Iterates over every coordinate in the route and checks the Haversine
        distance to the incident. If any point is within the threshold, the
        incident is considered to be on the route.
        """
        for point_lat, point_lng in route_points:
            distance = haversine(incident_lat, incident_lng, point_lat, point_lng)
            if distance <= _ROUTE_INCIDENT_THRESHOLD_METRES:
                return True
        return False

    @staticmethod
    def _build_message(event: IncidentEvent) -> str:
        severity_label = event.severity.capitalize()
        return (
            f"[{severity_label}] {event.type.replace('_', ' ').title()} reported "
            f"near your location. Stay alert and consider an alternate route."
        )