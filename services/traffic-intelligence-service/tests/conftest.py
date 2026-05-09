import sys
import os
import numpy as np
import pytest
from unittest.mock import MagicMock

# Tell Python where to find the app modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Override environment variables for testing.
# During tests, Docker is not running so the real PostgreSQL container
# is not available. We replace DATABASE_URL with a dummy value.
# The real DB is mocked anyway so this URL is never actually used.
os.environ["DATABASE_URL"] = "postgresql://urbanflow:test@localhost:5432/urbanflow_traffic_test"
os.environ["MODEL_PATH"]   = "/tmp/test_model.pkl"
os.environ["SECRET_KEY"]   = "test_secret_key"


@pytest.fixture
def mock_model_bundle():
    """
    A fake model bundle that mimics what load_model() returns.
    predict_proba must return a numpy array — not a plain list —
    because ml_model.py calls .max() on it which is a numpy method.
    """
    mock_clf = MagicMock()
    mock_clf.predict.return_value       = [2]
    mock_clf.predict_proba.return_value = np.array([[0.05, 0.05, 0.87, 0.03]])

    mock_encoder = MagicMock()
    mock_encoder.inverse_transform.return_value = ["High"]
    mock_encoder.classes_ = ["Low", "Medium", "High", "Very High"]

    return {"model": mock_clf, "label_encoder": mock_encoder}