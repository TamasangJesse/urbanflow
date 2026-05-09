import sys
import os

# Tell Python where to find the app modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "app"))

# Override environment variables for testing.
# During tests, Docker is not running so ${MONGO_USER} and
# ${MONGO_PASSWORD} placeholders never get filled in.
# We replace the entire URI with a simple no-auth local URI.
# The real DB is mocked anyway so this URI is never actually used.
os.environ["MONGO_URI"] = "mongodb://localhost:27017"
os.environ["MONGO_DB"] = "urbanflow_test"
os.environ["REDIS_HOST"] = "localhost"
os.environ["REDIS_PORT"] = "6379"
os.environ["SECRET_KEY"] = "test_secret_key"