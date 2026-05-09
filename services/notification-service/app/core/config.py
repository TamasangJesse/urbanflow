from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Redis
    redis_url: str = "redis://localhost:6379"

    # Service
    service_port: int = 8003

    # Redis Streams
    incident_stream_name: str = "incident_stream"
    stream_consumer_group: str = "notification_group"
    stream_consumer_name: str = "notification_consumer_1"

    # Notification TTL — 24 hours (matches document spec)
    notification_ttl_seconds: int = 86400

    # Geofencing — 5 km radius (matches document spec)
    geofence_radius_metres: float = 5000.0

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()