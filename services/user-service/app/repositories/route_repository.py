from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import SavedRoute
from typing import List
import uuid


class RouteRepository:
    """Hides all SavedRoute database logic. Service layer never writes raw SQL."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def save_route(self, user_id: str, origin: str, destination: str) -> SavedRoute:
        """Save a new route for a user."""
        route = SavedRoute(
            user_id=uuid.UUID(user_id),
            origin=origin,
            destination=destination,
        )
        self.db.add(route)
        await self.db.commit()
        await self.db.refresh(route)
        return route

    async def find_routes_by_user(self, user_id: str) -> List[SavedRoute]:
        """Return all saved routes for a given user."""
        result = await self.db.execute(
            select(SavedRoute).where(SavedRoute.user_id == uuid.UUID(user_id))
        )
        return result.scalars().all()

    async def delete_route(self, route_id: str, user_id: str) -> bool:
        """Delete a specific route — only if it belongs to the requesting user."""
        result = await self.db.execute(
            select(SavedRoute).where(
                SavedRoute.id == uuid.UUID(route_id),
                SavedRoute.user_id == uuid.UUID(user_id),
            )
        )
        route = result.scalar_one_or_none()
        if not route:
            return False
        await self.db.delete(route)
        await self.db.commit()
        return True