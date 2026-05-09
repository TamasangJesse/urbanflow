import sys
import os

# Tell Python where to find the app modules.
# Tests live in notification-service/tests/ and app code lives in
# notification-service/app/ — this makes sure imports like
# "from app.core.haversine import haversine" resolve correctly.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Override environment variables for testing.
# During tests, Docker is not running so Redis is not available.
# The real Redis is mocked in every test anyway so these values
# are never actually used to make a connection.
os.environ["REDIS_URL"] = "redis://localhost:6379"
os.environ["SERVICE_PORT"] = "8003"
os.environ["INCIDENT_STREAM_NAME"] = "incident_stream"
os.environ["STREAM_CONSUMER_GROUP"] = "notification_group"
os.environ["STREAM_CONSUMER_NAME"] = "notification_consumer_1"
os.environ["NOTIFICATION_TTL_SECONDS"] = "86400"
os.environ["GEOFENCE_RADIUS_METRES"] = "5000.0"