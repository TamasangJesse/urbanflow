
import json
from app.redis_client import redis_client


from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas import (
    UserProfileResponse,
    UpdateProfileRequest,
    UpdateLocationRequest,
    SaveRouteRequest,
    SavedRoutesResponse,
    SavedRouteResponse,
)
from app.repositories.user_repository import UserRepository
from app.repositories.route_repository import RouteRepository
from app.auth import get_current_user_id

router = APIRouter(prefix="/users", tags=["Users"])


# ─── Profile ────────────────────────────────────────────────────

@router.get("/{user_id}", response_model=UserProfileResponse)
async def get_profile(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
):
    """
    GET /users/{id}
    Returns a user's profile information from PostgreSQL.
    """
    repo = UserRepository(db)
    user = await repo.find_by_id(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.put("/{user_id}", response_model=UserProfileResponse)
async def update_profile(
    user_id: str,
    body: UpdateProfileRequest,
    db: AsyncSession = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
):
    """
    PUT /users/{id}
    Updates the user's name or preferences in PostgreSQL.
    Only the owner can update their own profile.
    """
    if current_user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot update another user's profile")

    repo = UserRepository(db)
    user = await repo.update_user(user_id=user_id, full_name=body.full_name)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
):
    """
    DELETE /users/{id}
    Permanently removes a user and all associated data.
    Only the owner can delete their own account.
    """
    if current_user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot delete another user's account")

    repo = UserRepository(db)
    deleted = await repo.delete_user(user_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")


# ─── Location ───────────────────────────────────────────────────

'''@router.put("/{user_id}/location", status_code=status.HTTP_200_OK)
async def update_location(
    user_id: str,
    body: UpdateLocationRequest,
    db: AsyncSession = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
):
    """
    PUT /users/{id}/location
    Updates the user's current GPS coordinates.
    Used by the Notification Service for geofencing.
    """
    if current_user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot update another user's location")

    repo = UserRepository(db)
    await repo.update_location(user_id=user_id, latitude=body.latitude, longitude=body.longitude)
    return {"message": "Location updated"}'''



@router.put("/{user_id}/location", status_code=status.HTTP_200_OK)
async def update_location(
    user_id: str,
    body: UpdateLocationRequest,
    db: AsyncSession = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
):
    if current_user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot update another user's location")

    # Save to PostgreSQL
    repo = UserRepository(db)
    await repo.update_location(user_id=user_id, latitude=body.latitude, longitude=body.longitude)

    # Build Redis payload
    redis_payload = {"latitude": body.latitude, "longitude": body.longitude}
    if body.route_points:
        redis_payload["route_points"] = body.route_points

    # Save to Redis for Notification Service geofencing
    await redis_client.setex(
        f"user_session:{user_id}",
        86400,
        json.dumps(redis_payload)
    )

    return {"message": "Location updated"}

# ─── Saved Routes ────────────────────────────────────────────────

@router.get("/{user_id}/routes", response_model=SavedRoutesResponse)
async def get_saved_routes(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
):
    """
    GET /users/{id}/routes
    Returns all routes the user has saved.
    """
    repo = RouteRepository(db)
    routes = await repo.find_routes_by_user(user_id)
    return SavedRoutesResponse(routes=routes)


@router.post("/{user_id}/routes", response_model=SavedRouteResponse, status_code=status.HTTP_201_CREATED)
async def save_route(
    user_id: str,
    body: SaveRouteRequest,
    db: AsyncSession = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
):
    """
    POST /users/{id}/routes
    Saves a new route for the user.
    """
    if current_user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot save routes for another user")

    repo = RouteRepository(db)
    route = await repo.save_route(user_id=user_id, origin=body.origin, destination=body.destination)
    return route


@router.delete("/{user_id}/routes/{route_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_route(
    user_id: str,
    route_id: str,
    db: AsyncSession = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
):
    """
    DELETE /users/{id}/routes/{route_id}
    Removes a saved route — only if it belongs to this user.
    """
    if current_user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot delete another user's routes")

    repo = RouteRepository(db)
    deleted = await repo.delete_route(route_id=route_id, user_id=user_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Route not found")