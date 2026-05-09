from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # -------------------------------------------------------------------------
    # JWT — must match the User Service SECRET_KEY exactly.
    # If these differ, every token the User Service issues will be rejected
    # by the gateway. This is the most common mistake in distributed JWT auth.
    # -------------------------------------------------------------------------
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # -------------------------------------------------------------------------
    # Redis — runs as a container in the shared Docker network.
    # Used exclusively for the token blacklist (tokens invalidated on logout).
    # -------------------------------------------------------------------------
    REDIS_URL: str

    # -------------------------------------------------------------------------
    # Downstream service URLs — Docker container names, never localhost.
    # Inside Docker, localhost resolves to the gateway container itself.
    # -------------------------------------------------------------------------
    USER_SERVICE_URL: str
    TRAFFIC_SERVICE_URL: str
    NOTIFICATION_SERVICE_URL: str
    INCIDENT_SERVICE_URL: str

    class Config:
        env_file = ".env"


# Single instance imported everywhere — loaded once at startup.
settings = Settings()