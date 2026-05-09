from pydantic import BaseModel, EmailStr
from datetime import datetime
from uuid import UUID
from typing import Optional, List


# ─── Auth Schemas ───────────────────────────────────────────────

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str


class TokenVerifyResponse(BaseModel):
    valid: bool
    user_id: Optional[str] = None


# ─── User Profile Schemas ────────────────────────────────────────

class UserProfileResponse(BaseModel):
    id: UUID
    email: str
    full_name: str
    created_at: datetime

    class Config:
        from_attributes = True


class UpdateProfileRequest(BaseModel):
    full_name: Optional[str] = None


# ─── Location Schemas ────────────────────────────────────────────

class UpdateLocationRequest(BaseModel):
    latitude: float
    longitude: float


# ─── Saved Route Schemas ─────────────────────────────────────────

class SaveRouteRequest(BaseModel):
    origin: str
    destination: str


class SavedRouteResponse(BaseModel):
    id: UUID
    origin: str
    destination: str
    created_at: datetime

    class Config:
        from_attributes = True


class SavedRoutesResponse(BaseModel):
    routes: List[SavedRouteResponse]