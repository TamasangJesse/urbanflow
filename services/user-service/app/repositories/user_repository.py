from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import User, UserLocation
from typing import Optional
import uuid


class UserRepository:
    """Hides all User and UserLocation database logic. Service layer never writes raw SQL."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def save_user(self, email: str, password_hash: str, full_name: str) -> User:
        """Create and persist a new user record."""
        user = User(email=email, password_hash=password_hash, full_name=full_name)
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def find_by_email(self, email: str) -> Optional[User]:
        """Look up a user by their email address."""
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def find_by_id(self, user_id: str) -> Optional[User]:
        """Look up a user by their UUID."""
        result = await self.db.execute(select(User).where(User.id == uuid.UUID(user_id)))
        return result.scalar_one_or_none()

    async def update_user(self, user_id: str, full_name: str) -> Optional[User]:
        """Update a user's profile fields."""
        user = await self.find_by_id(user_id)
        if not user:
            return None
        if full_name:
            user.full_name = full_name
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def delete_user(self, user_id: str) -> bool:
        """Permanently delete a user and all related data (cascade handles the rest)."""
        user = await self.find_by_id(user_id)
        if not user:
            return False
        await self.db.delete(user)
        await self.db.commit()
        return True

    async def update_location(self, user_id: str, latitude: float, longitude: float) -> UserLocation:
        """Upsert the user's current GPS coordinates."""
        result = await self.db.execute(
            select(UserLocation).where(UserLocation.user_id == uuid.UUID(user_id))
        )
        location = result.scalar_one_or_none()

        if location:
            location.latitude = latitude
            location.longitude = longitude
        else:
            location = UserLocation(
                user_id=uuid.UUID(user_id),
                latitude=latitude,
                longitude=longitude,
            )
            self.db.add(location)

        await self.db.commit()
        await self.db.refresh(location)
        return location