from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas import RegisterRequest, LoginRequest, TokenResponse, TokenVerifyResponse
from app.repositories.user_repository import UserRepository
from app.auth import hash_password, verify_password, create_access_token, get_current_user_id

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register_user(body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """
    POST /auth/register
    Validates email uniqueness, hashes password with bcrypt,
    saves to PostgreSQL, returns a JWT access token.
    """
    repo = UserRepository(db)

    existing = await repo.find_by_email(body.email)
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    hashed = hash_password(body.password)
    user = await repo.save_user(email=body.email, password_hash=hashed, full_name=body.full_name)

    token = create_access_token(user_id=str(user.id))
    return TokenResponse(access_token=token, user_id=str(user.id))


@router.post("/login", response_model=TokenResponse)
async def login_user(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    """
    POST /auth/login
    Verifies credentials against the stored bcrypt hash,
    returns a signed JWT access token.
    """
    repo = UserRepository(db)

    user = await repo.find_by_email(body.email)
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    token = create_access_token(user_id=str(user.id))
    return TokenResponse(access_token=token, user_id=str(user.id))


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout_user(current_user_id: str = Depends(get_current_user_id)):
    """
    POST /auth/logout
    In a full implementation, the token would be added to a Redis blacklist here.
    For now, logout is handled client-side by discarding the token.
    Redis blacklist integration will be wired in when the Redis container is added.
    """
    return {"message": "Logged out successfully"}


@router.get("/verify", response_model=TokenVerifyResponse)
async def verify_token(current_user_id: str = Depends(get_current_user_id)):
    """
    GET /auth/verify
    Called by the API Gateway to confirm whether a JWT is still valid.
    Returns the user_id so the gateway can forward it downstream.
    """
    return TokenVerifyResponse(valid=True, user_id=current_user_id)