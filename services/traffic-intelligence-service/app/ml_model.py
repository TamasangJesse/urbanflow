"""
ml_model.py
Traffic Intelligence Service — UrbanFlow
-----------------------------------------
Self-contained ML pipeline. Three responsibilities only:
  1. encode_features()  — convert raw record dicts into a feature matrix
  2. train_model()      — read from DB, train RandomForestClassifier, save model.pkl
  3. load_model()       — load model.pkl from disk for prediction

Nothing in here knows about HTTP, FastAPI, or request/response schemas.
main.py calls these functions — they never call main.py.

model.pkl is saved to /app/ml_model/model.pkl inside the container.
This path is defined once in MODEL_PATH below — change it here if needed.
"""

import os
import math
import logging
import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

from app.queries import TrafficQueryRepository

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# model.pkl lives in the ml_model/ folder at the project root inside container
# ---------------------------------------------------------------------------
MODEL_PATH = os.getenv("MODEL_PATH", "/app/ml_model/model.pkl")

# ---------------------------------------------------------------------------
# Feature columns the model trains and predicts on.
# ---------------------------------------------------------------------------
FEATURE_COLUMNS = ["hour", "day_of_week_encoded", "latitude", "longitude"]
TARGET_COLUMN   = "congestion_level"

DAY_ORDER = {
    "Monday": 0, "Tuesday": 1, "Wednesday": 2, "Thursday": 3,
    "Friday": 4, "Saturday": 5, "Sunday": 6,
}

# ---------------------------------------------------------------------------
# Radius within which an incident affects a predicted location.
# 1.0 km covers most Yaoundé intersections and their surroundings.
# ---------------------------------------------------------------------------
BOOST_RADIUS_KM = 1.0


# ---------------------------------------------------------------------------
# 1. FEATURE ENCODING
# ---------------------------------------------------------------------------

def encode_features(records: list[dict]) -> pd.DataFrame:
    """
    Convert a list of raw traffic record dicts into a clean feature DataFrame.
    Called by both train_model() and predict_congestion().
    """
    df = pd.DataFrame(records)
    df["day_of_week_encoded"] = df["day_of_week"].map(DAY_ORDER)

    if df["day_of_week_encoded"].isna().any():
        bad = df[df["day_of_week_encoded"].isna()]["day_of_week"].unique().tolist()
        raise ValueError(
            f"Unknown day_of_week values found: {bad}. "
            f"Expected one of: {list(DAY_ORDER.keys())}"
        )

    return df[FEATURE_COLUMNS]


# ---------------------------------------------------------------------------
# 2. TRAIN
# ---------------------------------------------------------------------------

def train_model() -> dict:
    """
    Full training pipeline:
      1. Load all records from PostgreSQL
      2. Encode features
      3. Train/test split (80/20)
      4. Fit RandomForestClassifier
      5. Save model + label encoder to MODEL_PATH

    Returns a summary dict consumed by main.py.
    Raises RuntimeError if fewer than 10 records exist.
    """
    logger.info("Training pipeline started — loading data from PostgreSQL ...")

    repo    = TrafficQueryRepository()
    records = repo.get_all_traffic_records()

    if len(records) < 10:
        raise RuntimeError(
            f"Not enough training data — found {len(records)} records. "
            "Run seed_traffic_data.py first."
        )

    logger.info(f"Loaded {len(records)} records from traffic_data.")

    X = encode_features(records)

    df_target     = pd.DataFrame(records)
    label_encoder = LabelEncoder()
    y             = label_encoder.fit_transform(df_target[TARGET_COLUMN])

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y,
    )

    clf = RandomForestClassifier(
        n_estimators=100,
        max_depth=12,
        random_state=42,
        n_jobs=-1,
    )
    clf.fit(X_train, y_train)

    y_pred = clf.predict(X_test)
    report = classification_report(
        y_test, y_pred,
        target_names=label_encoder.classes_,
        output_dict=True,
    )
    logger.info(
        "Classification report:\n%s",
        classification_report(y_test, y_pred, target_names=label_encoder.classes_),
    )

    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    joblib.dump({"model": clf, "label_encoder": label_encoder}, MODEL_PATH)
    logger.info(f"Model saved to {MODEL_PATH}")

    return {
        "status":        "trained",
        "records_used":  len(records),
        "test_accuracy": round(report["accuracy"], 4),
        "model_path":    MODEL_PATH,
        "classes":       label_encoder.classes_.tolist(),
    }


# ---------------------------------------------------------------------------
# 3. PROXIMITY HELPERS
# ---------------------------------------------------------------------------

def _haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """
    Calculate the great-circle distance in km between two lat/lng points.
    Used to check if an incident is close enough to affect a predicted location.
    """
    R    = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a    = (math.sin(dlat / 2) ** 2
            + math.cos(math.radians(lat1))
            * math.cos(math.radians(lat2))
            * math.sin(dlng / 2) ** 2)
    return R * 2 * math.asin(math.sqrt(a))


def _find_nearby_boost(
    latitude: float,
    longitude: float,
    active_incident_boosts: dict,
) -> dict | None:
    """
    Return the highest-severity boost within BOOST_RADIUS_KM of the given
    coordinates, or None if no active incidents are nearby.
    If multiple incidents are within range, returns the most severe one.
    """
    severity_rank = {"Medium": 1, "High": 2, "Very High": 3}
    best: dict | None = None

    for incident_id, boost in active_incident_boosts.items():
        distance = _haversine_km(
            latitude, longitude,
            boost["latitude"], boost["longitude"],
        )
        if distance <= BOOST_RADIUS_KM:
            if best is None or (
                severity_rank.get(boost["congestion_level"], 0)
                > severity_rank.get(best["congestion_level"], 0)
            ):
                best = boost

    return best


# ---------------------------------------------------------------------------
# 4. LOAD + PREDICT
# ---------------------------------------------------------------------------

def load_model() -> dict:
    """
    Load the saved model and label encoder from MODEL_PATH.
    Called once at startup by main.py and cached — not reloaded per request.
    """
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(
            f"model.pkl not found at {MODEL_PATH}. "
            "The service should have trained it at startup — check logs."
        )
    return joblib.load(MODEL_PATH)


def predict_congestion(
    location_name: str,
    latitude: float,
    longitude: float,
    day_of_week: str,
    hour: int,
    model_bundle: dict,
    active_incident_boosts: dict | None = None,
) -> dict:
    """
    Run a single prediction using the loaded model bundle.
    Called by GET /predict on every request.

    Checks active_incident_boosts FIRST before calling the ML model.
    Boost matching is done by proximity (lat/lng within BOOST_RADIUS_KM),
    not by location name. Boosts have no expiry — they stay until the
    incident is resolved via the Incident Report Service.

    Returns:
        {
          "location":         str,
          "day_of_week":      str,
          "hour":             int,
          "congestion_level": str,    e.g. "High"
          "confidence":       float,  e.g. 0.87
          "boosted":          bool    True if an incident override is active
        }
    """
    # ── Incident boost check — runs BEFORE the ML model ──────────────────────
    if active_incident_boosts:
        matched_boost = _find_nearby_boost(latitude, longitude, active_incident_boosts)
        if matched_boost:
            logger.info(
                "Incident boost active near '%s' — returning '%s' without calling model.",
                location_name, matched_boost["congestion_level"],
            )
            return {
                "location":         location_name,
                "day_of_week":      day_of_week,
                "hour":             hour,
                "congestion_level": matched_boost["congestion_level"],
                "confidence":       1.0,
                "boosted":          True,
            }

    # ── ML model prediction ───────────────────────────────────────────────────
    clf           = model_bundle["model"]
    label_encoder = model_bundle["label_encoder"]

    record = [{
        "hour":        hour,
        "day_of_week": day_of_week,
        "latitude":    latitude,
        "longitude":   longitude,
    }]
    X = encode_features(record)

    prediction_idx   = clf.predict(X)[0]
    probabilities    = clf.predict_proba(X)[0]
    confidence       = round(float(probabilities.max()), 4)
    congestion_label = label_encoder.inverse_transform([prediction_idx])[0]

    return {
        "location":         location_name,
        "day_of_week":      day_of_week,
        "hour":             hour,
        "congestion_level": congestion_label,
        "confidence":       confidence,
        "boosted":          False,
    }