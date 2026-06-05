"""
test_ml.py
Traffic Intelligence Service — UrbanFlow
-----------------------------------------
Extended tests covering:
  - encode_features()        (ml_model.py)
  - _haversine_km()          (ml_model.py)
  - _find_nearby_boost()     (ml_model.py)
  - predict_congestion()     (ml_model.py)
  - Extended endpoint tests  (routes.py)

Run with: pytest tests/ -v
"""

import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from datetime import datetime

from app.main import app
from app.ml_model import (
    encode_features,
    _haversine_km,
    _find_nearby_boost,
    predict_congestion,
)

client = TestClient(app)


# ---------------------------------------------------------------------------
# SHARED FIXTURES
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_traffic_record():
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
    return {
        "status":        "trained",
        "records_used":  6384,
        "test_accuracy": 0.89,
        "model_path":    "/tmp/test_model.pkl",
        "classes":       ["High", "Low", "Medium", "Very High"],
    }


@pytest.fixture
def sample_records():
    return [
        {"hour": 8,  "day_of_week": "Monday",    "latitude": 3.883, "longitude": 11.515},
        {"hour": 18, "day_of_week": "Friday",     "latitude": 3.873, "longitude": 11.532},
        {"hour": 0,  "day_of_week": "Sunday",     "latitude": 3.828, "longitude": 11.490},
        {"hour": 12, "day_of_week": "Wednesday",  "latitude": 3.878, "longitude": 11.505},
    ]


# ---------------------------------------------------------------------------
# encode_features()
# ---------------------------------------------------------------------------

class TestEncodeFeatures:

    def test_returns_correct_columns(self, sample_records):
        df = encode_features(sample_records)
        assert list(df.columns) == ["hour", "day_of_week_encoded", "latitude", "longitude"]

    def test_correct_row_count(self, sample_records):
        df = encode_features(sample_records)
        assert len(df) == len(sample_records)

    def test_monday_encodes_to_0(self):
        df = encode_features([{"hour": 8, "day_of_week": "Monday", "latitude": 3.88, "longitude": 11.51}])
        assert df["day_of_week_encoded"].iloc[0] == 0

    def test_sunday_encodes_to_6(self):
        df = encode_features([{"hour": 8, "day_of_week": "Sunday", "latitude": 3.88, "longitude": 11.51}])
        assert df["day_of_week_encoded"].iloc[0] == 6

    def test_friday_encodes_to_4(self):
        df = encode_features([{"hour": 8, "day_of_week": "Friday", "latitude": 3.88, "longitude": 11.51}])
        assert df["day_of_week_encoded"].iloc[0] == 4

    def test_invalid_day_raises_value_error(self):
        with pytest.raises(ValueError, match="Unknown day_of_week"):
            encode_features([{"hour": 8, "day_of_week": "Funday", "latitude": 3.88, "longitude": 11.51}])

    def test_hour_preserved_correctly(self):
        df = encode_features([{"hour": 18, "day_of_week": "Friday", "latitude": 3.88, "longitude": 11.51}])
        assert df["hour"].iloc[0] == 18

    def test_coordinates_preserved(self):
        df = encode_features([{"hour": 8, "day_of_week": "Monday", "latitude": 3.8731, "longitude": 11.5321}])
        assert abs(df["latitude"].iloc[0]  - 3.8731)  < 0.0001
        assert abs(df["longitude"].iloc[0] - 11.5321) < 0.0001


# ---------------------------------------------------------------------------
# _haversine_km()
# ---------------------------------------------------------------------------

class TestHaversine:

    def test_same_point_is_zero(self):
        assert _haversine_km(3.883, 11.515, 3.883, 11.515) == pytest.approx(0.0, abs=0.001)

    def test_known_distance_bastos_to_warda(self):
        dist = _haversine_km(3.8830, 11.5150, 3.8731, 11.5321)
        assert 1.5 < dist < 2.5

    def test_distance_is_symmetric(self):
        d1 = _haversine_km(3.883, 11.515, 3.873, 11.532)
        d2 = _haversine_km(3.873, 11.532, 3.883, 11.515)
        assert d1 == pytest.approx(d2, abs=0.001)

    def test_short_distance_under_1km(self):
        dist = _haversine_km(3.8830, 11.5150, 3.8835, 11.5155)
        assert dist < 1.0

    def test_long_distance_across_city(self):
        dist = _haversine_km(3.8830, 11.5150, 3.7823, 11.5134)
        assert dist > 8.0


# ---------------------------------------------------------------------------
# _find_nearby_boost()
# ---------------------------------------------------------------------------

class TestFindNearbyBoost:

    def test_returns_none_when_no_boosts(self):
        assert _find_nearby_boost(3.883, 11.515, {}) is None

    def test_returns_boost_within_radius(self):
        boosts = {"inc001": {"congestion_level": "Very High", "latitude": 3.8830, "longitude": 11.5150}}
        result = _find_nearby_boost(3.8830, 11.5150, boosts)
        assert result is not None
        assert result["congestion_level"] == "Very High"

    def test_returns_none_outside_radius(self):
        boosts = {"inc001": {"congestion_level": "High", "latitude": 3.9500, "longitude": 11.6000}}
        assert _find_nearby_boost(3.8830, 11.5150, boosts) is None

    def test_returns_most_severe_when_multiple_nearby(self):
        boosts = {
            "inc001": {"congestion_level": "Medium",   "latitude": 3.8830, "longitude": 11.5150},
            "inc002": {"congestion_level": "Very High", "latitude": 3.8832, "longitude": 11.5152},
        }
        result = _find_nearby_boost(3.8830, 11.5150, boosts)
        assert result["congestion_level"] == "Very High"

    def test_ignores_far_boosts(self):
        boosts = {"inc001": {"congestion_level": "High", "latitude": 3.7000, "longitude": 11.4000}}
        assert _find_nearby_boost(3.8830, 11.5150, boosts) is None


# ---------------------------------------------------------------------------
# predict_congestion()
# ---------------------------------------------------------------------------

class TestPredictCongestion:

    def test_returns_ml_prediction_when_no_boosts(self, mock_model_bundle):
        result = predict_congestion(
            location_name="Bastos", latitude=3.8830, longitude=11.5150,
            day_of_week="Monday", hour=8,
            model_bundle=mock_model_bundle, active_incident_boosts={},
        )
        assert result["congestion_level"] == "High"
        assert result["boosted"]          == False

    def test_returns_boost_when_incident_nearby(self, mock_model_bundle):
        boosts = {"inc001": {"congestion_level": "Very High", "latitude": 3.8830, "longitude": 11.5150}}
        result = predict_congestion(
            location_name="Bastos", latitude=3.8830, longitude=11.5150,
            day_of_week="Monday", hour=8,
            model_bundle=mock_model_bundle, active_incident_boosts=boosts,
        )
        assert result["congestion_level"] == "Very High"
        assert result["boosted"]          == True
        assert result["confidence"]       == 1.0

    def test_response_contains_all_fields(self, mock_model_bundle):
        result = predict_congestion(
            location_name="Bastos", latitude=3.8830, longitude=11.5150,
            day_of_week="Monday", hour=8, model_bundle=mock_model_bundle,
        )
        for field in ["location", "day_of_week", "hour", "congestion_level", "confidence", "boosted"]:
            assert field in result

    def test_ml_not_called_when_boosted(self, mock_model_bundle):
        boosts = {"inc001": {"congestion_level": "Very High", "latitude": 3.8830, "longitude": 11.5150}}
        predict_congestion(
            location_name="Bastos", latitude=3.8830, longitude=11.5150,
            day_of_week="Monday", hour=8,
            model_bundle=mock_model_bundle, active_incident_boosts=boosts,
        )
        mock_model_bundle["model"].predict.assert_not_called()

    def test_works_with_none_boosts(self, mock_model_bundle):
        result = predict_congestion(
            location_name="Bastos", latitude=3.8830, longitude=11.5150,
            day_of_week="Monday", hour=8,
            model_bundle=mock_model_bundle, active_incident_boosts=None,
        )
        assert result["boosted"] == False


# ---------------------------------------------------------------------------
# Extended endpoint tests
# ---------------------------------------------------------------------------

class TestPredictExtended:

    VALID_PARAMS = {
        "location_name": "Carrefour Warda",
        "latitude":      3.8731,
        "longitude":     11.5321,
        "day_of_week":   "Friday",
        "hour":          18,
    }

    def test_boosted_false_when_no_incidents(self, mock_model_bundle):
        with patch("app.state._model_bundle", mock_model_bundle), \
             patch("app.state.active_incident_boosts", {}):
            response = client.get("/predict", params=self.VALID_PARAMS)
        assert response.json()["boosted"] == False

    def test_boosted_true_when_incident_nearby(self, mock_model_bundle):
        boosts = {"inc001": {"congestion_level": "Very High", "latitude": 3.8731, "longitude": 11.5321}}
        with patch("app.state._model_bundle", mock_model_bundle), \
             patch("app.state.active_incident_boosts", boosts):
            response = client.get("/predict", params=self.VALID_PARAMS)
        data = response.json()
        assert data["boosted"]          == True
        assert data["congestion_level"] == "Very High"
        assert data["confidence"]       == 1.0

    def test_hour_boundary_0(self, mock_model_bundle):
        params = {**self.VALID_PARAMS, "hour": 0}
        with patch("app.state._model_bundle", mock_model_bundle):
            assert client.get("/predict", params=params).status_code == 200

    def test_hour_boundary_23(self, mock_model_bundle):
        params = {**self.VALID_PARAMS, "hour": 23}
        with patch("app.state._model_bundle", mock_model_bundle):
            assert client.get("/predict", params=params).status_code == 200


class TestPostTrafficDataExtended:

    VALID_PAYLOAD = {
        "location_name": "Bastos", "latitude": 3.8830, "longitude": 11.5150,
        "day_of_week": "Monday", "hour": 8, "congestion_level": "High", "source": "api",
    }

    def test_db_error_returns_500(self):
        with patch("app.routes.TrafficCommandRepository") as MockRepo:
            MockRepo.return_value.insert_traffic_record.side_effect = Exception("DB error")
            response = client.post("/traffic-data", json=self.VALID_PAYLOAD)
        assert response.status_code == 500

    def test_all_valid_days_accepted(self, mock_traffic_record):
        for day in ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]:
            payload = {**self.VALID_PAYLOAD, "day_of_week": day}
            with patch("app.routes.TrafficCommandRepository") as MockRepo:
                MockRepo.return_value.insert_traffic_record.return_value = mock_traffic_record
                assert client.post("/traffic-data", json=payload).status_code == 201

    def test_all_valid_congestion_levels_accepted(self, mock_traffic_record):
        for level in ["Low", "Medium", "High", "Very High"]:
            payload = {**self.VALID_PAYLOAD, "congestion_level": level}
            updated = {**mock_traffic_record, "congestion_level": level}
            with patch("app.routes.TrafficCommandRepository") as MockRepo:
                MockRepo.return_value.insert_traffic_record.return_value = updated
                assert client.post("/traffic-data", json=payload).status_code == 201

    def test_invalid_hour_negative(self):
        payload = {**self.VALID_PAYLOAD, "hour": -1}
        assert client.post("/traffic-data", json=payload).status_code == 422


class TestRetrainExtended:

    def test_returns_500_on_unexpected_error(self):
        with patch("app.routes.train_model", side_effect=Exception("Unexpected")):
            assert client.post("/model/retrain").status_code == 500

    def test_retrain_updates_state(self, mock_model_bundle, mock_training_summary):
        with patch("app.routes.train_model", return_value=mock_training_summary), \
             patch("app.routes.load_model",  return_value=mock_model_bundle):
            client.post("/model/retrain")
        import app.state as state
        assert state._training_summary == mock_training_summary


class TestModelStatusExtended:

    def test_not_trained_has_no_accuracy(self):
        with patch("app.state._model_bundle", None), \
             patch("app.state._training_summary", None):
            data = client.get("/model/status").json()
        assert data.get("test_accuracy") is None

    def test_contains_model_path_when_ready(self, mock_model_bundle, mock_training_summary):
        with patch("app.state._model_bundle", mock_model_bundle), \
             patch("app.state._training_summary", mock_training_summary):
            with patch("app.routes.TrafficQueryRepository") as MockRepo:
                MockRepo.return_value.get_record_count.return_value = 6384
                data = client.get("/model/status").json()
        assert data["model_path"] == "/tmp/test_model.pkl"