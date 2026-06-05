"""
test_traffic.py
Traffic Intelligence Service — UrbanFlow
-----------------------------------------
Unit and integration tests for all endpoints.

Tests are grouped by endpoint:
  - GET  /health
  - GET  /locations
  - GET  /traffic-data
  - POST /traffic-data
  - GET  /predict
  - GET  /model/status
  - POST /model/retrain

The database and ML model are fully mocked — no Docker, no PostgreSQL,
no model.pkl required. Tests run anywhere with just:
    pip install pytest pytest-mock httpx
    pytest tests/
"""

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from datetime import datetime

from app.main import app

client = TestClient(app)


# ---------------------------------------------------------------------------
# SHARED FIXTURES
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_traffic_record():
    """A realistic traffic record dict as returned by the repository."""
    return {
        "id":               1,
        "location_name":    "Bastos",
        "latitude":         3.8830,
        "longitude":        11.5150,
        "day_of_week":      "Monday",
        "hour":             8,
        "congestion_level": "High",
        "source":           "simulated",
        "created_at":       datetime(2026, 1, 1, 8, 0, 0),
    }


@pytest.fixture
def mock_training_summary():
    """A fake training summary dict as returned by train_model()."""
    return {
        "status":        "trained",
        "records_used":  6384,
        "test_accuracy": 0.89,
        "model_path":    "/tmp/test_model.pkl",
        "classes":       ["High", "Low", "Medium", "Very High"],
    }


# ---------------------------------------------------------------------------
# GET /health
# ---------------------------------------------------------------------------

class TestHealth:

    def test_health_returns_200(self):
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_response_body(self):
        response = client.get("/health")
        data = response.json()
        assert data["status"]  == "ok"
        assert data["service"] == "traffic-intelligence-service"


# ---------------------------------------------------------------------------
# GET /locations
# ---------------------------------------------------------------------------

class TestLocations:

    def test_get_locations_returns_200(self):
        with patch("app.routes.TrafficQueryRepository") as MockRepo:
            MockRepo.return_value.get_distinct_locations.return_value = [
                "Bastos", "Mokolo Market", "Rond Point Express"
            ]
            response = client.get("/locations")
        assert response.status_code == 200

    def test_get_locations_response_shape(self):
        expected = ["Bastos", "Mokolo Market", "Rond Point Express"]
        with patch("app.routes.TrafficQueryRepository") as MockRepo:
            MockRepo.return_value.get_distinct_locations.return_value = expected
            response = client.get("/locations")
        data = response.json()
        assert data["locations"] == expected
        assert data["total"]     == 3

    def test_get_locations_empty_db(self):
        with patch("app.routes.TrafficQueryRepository") as MockRepo:
            MockRepo.return_value.get_distinct_locations.return_value = []
            response = client.get("/locations")
        data = response.json()
        assert data["locations"] == []
        assert data["total"]     == 0


# ---------------------------------------------------------------------------
# GET /traffic-data
# ---------------------------------------------------------------------------

class TestGetTrafficData:

    def test_get_all_records_returns_200(self, mock_traffic_record):
        with patch("app.routes.TrafficQueryRepository") as MockRepo:
            MockRepo.return_value.get_all_traffic_records.return_value = [mock_traffic_record]
            response = client.get("/traffic-data")
        assert response.status_code == 200

    def test_get_all_records_returns_list(self, mock_traffic_record):
        with patch("app.routes.TrafficQueryRepository") as MockRepo:
            MockRepo.return_value.get_all_traffic_records.return_value = [mock_traffic_record]
            response = client.get("/traffic-data")
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["location_name"] == "Bastos"

    def test_get_records_filtered_by_location(self, mock_traffic_record):
        with patch("app.routes.TrafficQueryRepository") as MockRepo:
            MockRepo.return_value.get_traffic_records_by_location.return_value = [mock_traffic_record]
            response = client.get("/traffic-data?location=Bastos")
        assert response.status_code == 200
        data = response.json()
        assert data[0]["location_name"] == "Bastos"

    def test_get_records_empty_result(self):
        with patch("app.routes.TrafficQueryRepository") as MockRepo:
            MockRepo.return_value.get_all_traffic_records.return_value = []
            response = client.get("/traffic-data")
        assert response.status_code == 200
        assert response.json() == []


# ---------------------------------------------------------------------------
# POST /traffic-data
# ---------------------------------------------------------------------------

class TestPostTrafficData:

    def test_create_record_returns_201(self, mock_traffic_record):
        with patch("app.routes.TrafficCommandRepository") as MockRepo:
            MockRepo.return_value.insert_traffic_record.return_value = mock_traffic_record
            response = client.post("/traffic-data", json={
                "location_name":    "Bastos",
                "latitude":         3.8830,
                "longitude":        11.5150,
                "day_of_week":      "Monday",
                "hour":             8,
                "congestion_level": "High",
                "source":           "api",
            })
        assert response.status_code == 201

    def test_create_record_response_body(self, mock_traffic_record):
        with patch("app.routes.TrafficCommandRepository") as MockRepo:
            MockRepo.return_value.insert_traffic_record.return_value = mock_traffic_record
            response = client.post("/traffic-data", json={
                "location_name":    "Bastos",
                "latitude":         3.8830,
                "longitude":        11.5150,
                "day_of_week":      "Monday",
                "hour":             8,
                "congestion_level": "High",
                "source":           "api",
            })
        data = response.json()
        assert data["location_name"]    == "Bastos"
        assert data["congestion_level"] == "High"
        assert data["source"]           == "simulated"

    def test_create_record_invalid_day(self):
        response = client.post("/traffic-data", json={
            "location_name":    "Bastos",
            "latitude":         3.8830,
            "longitude":        11.5150,
            "day_of_week":      "Funday",   # invalid
            "hour":             8,
            "congestion_level": "High",
        })
        assert response.status_code == 422

    def test_create_record_invalid_congestion_level(self):
        response = client.post("/traffic-data", json={
            "location_name":    "Bastos",
            "latitude":         3.8830,
            "longitude":        11.5150,
            "day_of_week":      "Monday",
            "hour":             8,
            "congestion_level": "Extreme",  # invalid
        })
        assert response.status_code == 422

    def test_create_record_invalid_hour(self):
        response = client.post("/traffic-data", json={
            "location_name":    "Bastos",
            "latitude":         3.8830,
            "longitude":        11.5150,
            "day_of_week":      "Monday",
            "hour":             25,         # invalid, max is 23
            "congestion_level": "High",
        })
        assert response.status_code == 422

    def test_create_record_missing_required_field(self):
        response = client.post("/traffic-data", json={
            "location_name": "Bastos",
            # latitude missing
            "longitude":        11.5150,
            "day_of_week":      "Monday",
            "hour":             8,
            "congestion_level": "High",
        })
        assert response.status_code == 422


# ---------------------------------------------------------------------------
# GET /predict
# ---------------------------------------------------------------------------

class TestPredict:

    VALID_PARAMS = {
        "location_name": "Carrefour Warda",
        "latitude":      3.8731,
        "longitude":     11.5321,
        "day_of_week":   "Friday",
        "hour":          18,
    }

    def test_predict_returns_200_when_model_loaded(self, mock_model_bundle):
        with patch("app.state._model_bundle", mock_model_bundle):
            response = client.get("/predict", params=self.VALID_PARAMS)
        assert response.status_code == 200

    def test_predict_response_shape(self, mock_model_bundle):
        with patch("app.state._model_bundle", mock_model_bundle):
            response = client.get("/predict", params=self.VALID_PARAMS)
        data = response.json()
        assert "location"         in data
        assert "day_of_week"      in data
        assert "hour"             in data
        assert "congestion_level" in data
        assert "confidence"       in data

    def test_predict_returns_503_when_model_not_loaded(self):
        with patch("app.state._model_bundle", None):
            response = client.get("/predict", params=self.VALID_PARAMS)
        assert response.status_code == 503

    def test_predict_correct_location_in_response(self, mock_model_bundle):
        with patch("app.state._model_bundle", mock_model_bundle):
            response = client.get("/predict", params=self.VALID_PARAMS)
        assert response.json()["location"] == "Carrefour Warda"

    def test_predict_confidence_between_0_and_1(self, mock_model_bundle):
        with patch("app.state._model_bundle", mock_model_bundle):
            response = client.get("/predict", params=self.VALID_PARAMS)
        confidence = response.json()["confidence"]
        assert 0.0 <= confidence <= 1.0

    def test_predict_invalid_day_returns_422(self, mock_model_bundle):
        params = {**self.VALID_PARAMS, "day_of_week": "Funday"}
        with patch("app.state._model_bundle", mock_model_bundle):
            response = client.get("/predict", params=params)
        assert response.status_code == 422

    def test_predict_invalid_hour_returns_422(self, mock_model_bundle):
        params = {**self.VALID_PARAMS, "hour": 25}
        with patch("app.state._model_bundle", mock_model_bundle):
            response = client.get("/predict", params=params)
        assert response.status_code == 422


# ---------------------------------------------------------------------------
# GET /model/status
# ---------------------------------------------------------------------------

class TestModelStatus:

    def test_status_ready_when_model_loaded(self, mock_model_bundle, mock_training_summary):
        with patch("app.state._model_bundle", mock_model_bundle), \
             patch("app.state._training_summary", mock_training_summary):
            with patch("app.routes.TrafficQueryRepository") as MockRepo:
                MockRepo.return_value.get_record_count.return_value = 6384
                response = client.get("/model/status")
        assert response.status_code == 200
        assert response.json()["status"] == "ready"

    def test_status_not_trained_when_model_missing(self):
        with patch("app.state._model_bundle", None), \
             patch("app.state._training_summary", None):
            response = client.get("/model/status")
        assert response.status_code == 200
        assert response.json()["status"] == "not_trained"

    def test_status_contains_accuracy(self, mock_model_bundle, mock_training_summary):
        with patch("app.state._model_bundle", mock_model_bundle), \
             patch("app.state._training_summary", mock_training_summary):
            with patch("app.routes.TrafficQueryRepository") as MockRepo:
                MockRepo.return_value.get_record_count.return_value = 6384
                response = client.get("/model/status")
        assert response.json()["test_accuracy"] == 0.89

    def test_status_contains_classes(self, mock_model_bundle, mock_training_summary):
        with patch("app.state._model_bundle", mock_model_bundle), \
             patch("app.state._training_summary", mock_training_summary):
            with patch("app.routes.TrafficQueryRepository") as MockRepo:
                MockRepo.return_value.get_record_count.return_value = 6384
                response = client.get("/model/status")
        assert "classes" in response.json()


# ---------------------------------------------------------------------------
# POST /model/retrain
# ---------------------------------------------------------------------------

class TestRetrain:

    def test_retrain_returns_200(self, mock_model_bundle, mock_training_summary):
        with patch("app.routes.train_model", return_value=mock_training_summary), \
             patch("app.routes.load_model",  return_value=mock_model_bundle):
            response = client.post("/model/retrain")
        assert response.status_code == 200

    def test_retrain_response_shape(self, mock_model_bundle, mock_training_summary):
        with patch("app.routes.train_model", return_value=mock_training_summary), \
             patch("app.routes.load_model",  return_value=mock_model_bundle):
            response = client.post("/model/retrain")
        data = response.json()
        assert data["status"]        == "trained"
        assert data["records_used"]  == 6384
        assert data["test_accuracy"] == 0.89
        assert "classes"             in data
        assert "model_path"          in data

    def test_retrain_fails_with_no_data(self):
        with patch("app.routes.train_model", side_effect=RuntimeError("Not enough training data")):
            response = client.post("/model/retrain")
        assert response.status_code == 400
        assert "Not enough training data" in response.json()["detail"]

# ---------------------------------------------------------------------------
# FIXTURES FOR PREDICT TESTS (model bundle mock)
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_model_bundle():
    """Mock ML model bundle with predict and label encoder."""
    mock_model = MagicMock()
    mock_model.predict.return_value = ["High"]
    mock_model.predict_proba.return_value = [[0.05, 0.10, 0.75, 0.10]]

    mock_encoder = MagicMock()
    mock_encoder.classes_ = ["High", "Low", "Medium", "Very High"]
    mock_encoder.inverse_transform.return_value = ["High"]

    return {
        "model":         mock_model,
        "label_encoder": mock_encoder,
        "feature_cols":  ["latitude", "longitude", "hour", "day_encoded"],
    }


# ---------------------------------------------------------------------------
# INCIDENT BOOST TESTS
# ---------------------------------------------------------------------------

class TestIncidentBoost:

    VALID_PARAMS = {
        "location_name": "Carrefour Warda",
        "latitude":      3.8731,
        "longitude":     11.5321,
        "day_of_week":   "Friday",
        "hour":          18,
    }

    def test_boost_overrides_model_prediction(self, mock_model_bundle):
        boosted_state = {"Carrefour Warda": "Very High"}
        with patch("app.state._model_bundle", mock_model_bundle), \
             patch("app.state.active_incident_boosts", boosted_state):
            response = client.get("/predict", params=self.VALID_PARAMS)
        assert response.status_code == 200
        data = response.json()
        assert data["congestion_level"] == "Very High"
        assert data.get("source") == "incident_boost"

    def test_no_boost_falls_back_to_model(self, mock_model_bundle):
        with patch("app.state._model_bundle", mock_model_bundle), \
             patch("app.state.active_incident_boosts", {}):
            response = client.get("/predict", params=self.VALID_PARAMS)
        assert response.status_code == 200
        assert response.json()["congestion_level"] == "High"

    def test_boost_for_different_location_does_not_affect_request(self, mock_model_bundle):
        boosted_state = {"Mokolo Market": "Very High"}
        with patch("app.state._model_bundle", mock_model_bundle), \
             patch("app.state.active_incident_boosts", boosted_state):
            response = client.get("/predict", params=self.VALID_PARAMS)
        assert response.status_code == 200
        assert response.json()["congestion_level"] == "High"

    def test_multiple_boosts_only_matching_applied(self, mock_model_bundle):
        boosted_state = {
            "Mokolo Market":   "Very High",
            "Carrefour Warda": "High",
            "Biyem-Assi":      "Very High",
        }
        with patch("app.state._model_bundle", mock_model_bundle), \
             patch("app.state.active_incident_boosts", boosted_state):
            response = client.get("/predict", params=self.VALID_PARAMS)
        assert response.status_code == 200
        assert response.json()["congestion_level"] == "High"

    def test_boost_severity_high(self, mock_model_bundle):
        boosted_state = {"Carrefour Warda": "Very High"}
        with patch("app.state._model_bundle", mock_model_bundle), \
             patch("app.state.active_incident_boosts", boosted_state):
            response = client.get("/predict", params=self.VALID_PARAMS)
        assert response.json()["congestion_level"] == "Very High"

    def test_boost_severity_medium(self, mock_model_bundle):
        boosted_state = {"Carrefour Warda": "High"}
        with patch("app.state._model_bundle", mock_model_bundle), \
             patch("app.state.active_incident_boosts", boosted_state):
            response = client.get("/predict", params=self.VALID_PARAMS)
        assert response.json()["congestion_level"] == "High"

    def test_boost_severity_low(self, mock_model_bundle):
        boosted_state = {"Carrefour Warda": "Medium"}
        with patch("app.state._model_bundle", mock_model_bundle), \
             patch("app.state.active_incident_boosts", boosted_state):
            response = client.get("/predict", params=self.VALID_PARAMS)
        assert response.json()["congestion_level"] == "Medium"


# ---------------------------------------------------------------------------
# PREDICTION EDGE CASE TESTS
# ---------------------------------------------------------------------------

class TestPredictEdgeCases:

    def test_predict_peak_hour_friday(self, mock_model_bundle):
        params = {
            "location_name": "Mokolo Market",
            "latitude":      3.8712,
            "longitude":     11.5163,
            "day_of_week":   "Friday",
            "hour":          17,
        }
        with patch("app.state._model_bundle", mock_model_bundle), \
             patch("app.state.active_incident_boosts", {}):
            response = client.get("/predict", params=params)
        assert response.status_code == 200
        assert "congestion_level" in response.json()

    def test_predict_midnight_hour(self, mock_model_bundle):
        params = {
            "location_name": "Bastos",
            "latitude":      3.8830,
            "longitude":     11.5150,
            "day_of_week":   "Sunday",
            "hour":          0,
        }
        with patch("app.state._model_bundle", mock_model_bundle), \
             patch("app.state.active_incident_boosts", {}):
            response = client.get("/predict", params=params)
        assert response.status_code == 200

    def test_predict_all_valid_days(self, mock_model_bundle):
        days = ["Monday", "Tuesday", "Wednesday",
                "Thursday", "Friday", "Saturday", "Sunday"]
        params_base = {
            "location_name": "Bastos",
            "latitude":      3.8830,
            "longitude":     11.5150,
            "hour":          8,
        }
        with patch("app.state._model_bundle", mock_model_bundle), \
             patch("app.state.active_incident_boosts", {}):
            for day in days:
                response = client.get(
                    "/predict", params={**params_base, "day_of_week": day}
                )
                assert response.status_code == 200, f"Failed for day: {day}"

    def test_predict_boundary_hour_23(self, mock_model_bundle):
        params = {
            "location_name": "Carrefour Warda",
            "latitude":      3.8731,
            "longitude":     11.5321,
            "day_of_week":   "Monday",
            "hour":          23,
        }
        with patch("app.state._model_bundle", mock_model_bundle), \
             patch("app.state.active_incident_boosts", {}):
            response = client.get("/predict", params=params)
        assert response.status_code == 200

    def test_predict_response_includes_source_field(self, mock_model_bundle):
        params = {
            "location_name": "Bastos",
            "latitude":      3.8830,
            "longitude":     11.5150,
            "day_of_week":   "Monday",
            "hour":          8,
        }
        with patch("app.state._model_bundle", mock_model_bundle), \
             patch("app.state.active_incident_boosts", {}):
            response = client.get("/predict", params=params)
        assert "source" in response.json()


# ---------------------------------------------------------------------------
# DATA INTEGRITY TESTS
# ---------------------------------------------------------------------------

class TestDataIntegrity:

    def test_traffic_record_created_at_is_datetime(self, mock_traffic_record):
        assert isinstance(mock_traffic_record["created_at"], datetime)

    def test_traffic_record_has_all_required_fields(self, mock_traffic_record):
        required = [
            "id", "location_name", "latitude", "longitude",
            "day_of_week", "hour", "congestion_level", "source", "created_at"
        ]
        for field in required:
            assert field in mock_traffic_record, f"Missing field: {field}"

    def test_congestion_level_valid_values(self):
        valid_levels = {"Low", "Medium", "High", "Very High"}
        assert "High" in valid_levels

    def test_hour_within_valid_range(self, mock_traffic_record):
        assert 0 <= mock_traffic_record["hour"] <= 23

    def test_coordinates_within_yaounde_bounds(self, mock_traffic_record):
        assert 3.7  <= mock_traffic_record["latitude"]  <= 4.1
        assert 11.3 <= mock_traffic_record["longitude"] <= 11.7


# ---------------------------------------------------------------------------
# RETRAIN EDGE CASES
# ---------------------------------------------------------------------------

class TestRetrainEdgeCases:

    def test_retrain_updates_in_memory_model(self, mock_model_bundle, mock_training_summary):
        with patch("app.routes.train_model", return_value=mock_training_summary), \
             patch("app.routes.load_model",  return_value=mock_model_bundle), \
             patch("app.state") as mock_state:
            response = client.post("/model/retrain")
        assert response.status_code == 200

    def test_retrain_accuracy_above_threshold(self, mock_model_bundle, mock_training_summary):
        with patch("app.routes.train_model", return_value=mock_training_summary), \
             patch("app.routes.load_model",  return_value=mock_model_bundle):
            response = client.post("/model/retrain")
        assert response.json()["test_accuracy"] >= 0.75

    def test_retrain_returns_class_list(self, mock_model_bundle, mock_training_summary):
        with patch("app.routes.train_model", return_value=mock_training_summary), \
             patch("app.routes.load_model",  return_value=mock_model_bundle):
            response = client.post("/model/retrain")
        classes = response.json()["classes"]
        assert "High"      in classes
        assert "Low"       in classes
        assert "Medium"    in classes
        assert "Very High" in classes

    def test_retrain_server_error_returns_500(self):
        with patch("app.routes.train_model", side_effect=Exception("Unexpected DB failure")):
            response = client.post("/model/retrain")
        assert response.status_code == 500
