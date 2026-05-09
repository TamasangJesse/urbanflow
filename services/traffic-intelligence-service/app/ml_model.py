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
# Matches the ml_model/ folder in your VPS project structure
# ---------------------------------------------------------------------------
MODEL_PATH = os.getenv("MODEL_PATH", "/app/ml_model/model.pkl")

# ---------------------------------------------------------------------------
# Feature columns the model trains and predicts on.
# These must match exactly what the DB stores — no magic strings elsewhere.
# ---------------------------------------------------------------------------
FEATURE_COLUMNS = ["hour", "day_of_week_encoded", "latitude", "longitude"]
TARGET_COLUMN   = "congestion_level"

# Day of week encoding — consistent order, never changes between train and predict
DAY_ORDER = {
    "Monday": 0,
    "Tuesday": 1,
    "Wednesday": 2,
    "Thursday": 3,
    "Friday": 4,
    "Saturday": 5,
    "Sunday": 6,
}


# ---------------------------------------------------------------------------
# 1. FEATURE ENCODING
# ---------------------------------------------------------------------------

def encode_features(records: list[dict]) -> pd.DataFrame:
    """
    Convert a list of raw traffic record dicts into a clean feature DataFrame.
    Called by both train_model() and the /predict endpoint.

    Input:  list of dicts with keys: hour, day_of_week, latitude, longitude
    Output: DataFrame with columns matching FEATURE_COLUMNS exactly

    Encoding decisions:
      - day_of_week  → integer 0–6 via DAY_ORDER (ordinal, not one-hot)
                       Random Forest handles ordinal encoding well for cyclical
                       features like days of the week.
      - hour         → kept as integer 0–23, already numeric
      - lat/lng      → kept as float, give the model geographic signal
    """
    df = pd.DataFrame(records)

    df["day_of_week_encoded"] = df["day_of_week"].map(DAY_ORDER)

    # Guard: if any day_of_week value is not in DAY_ORDER, map() returns NaN
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
      1. Load all records from PostgreSQL via TrafficQueryRepository (query side)
      2. Encode features
      3. Encode target labels
      4. Train/test split (80/20)
      5. Fit RandomForestClassifier
      6. Log classification report
      7. Save model + label encoder together to MODEL_PATH as a single joblib file

    Returns a summary dict consumed by main.py to log startup info.
    Raises RuntimeError if the DB has fewer than 10 records — nothing to train on.
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

    # --- Features ---
    X = encode_features(records)

    # --- Target ---
    df_target = pd.DataFrame(records)
    label_encoder = LabelEncoder()
    y = label_encoder.fit_transform(df_target[TARGET_COLUMN])

    # --- Train/test split ---
    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=0.2,
        random_state=42,
        stratify=y,   # keeps class proportions balanced in both splits
    )

    # --- Fit ---
    clf = RandomForestClassifier(
        n_estimators=100,   # 100 trees — good balance of accuracy vs speed on VPS
        max_depth=12,       # prevents overfitting on our structured dataset
        random_state=42,
        n_jobs=-1,          # use all available CPU cores on the VPS
    )
    clf.fit(X_train, y_train)

    # --- Evaluate ---
    y_pred  = clf.predict(X_test)
    report  = classification_report(
        y_test, y_pred,
        target_names=label_encoder.classes_,
        output_dict=True,
    )
    logger.info(
        "Classification report:\n%s",
        classification_report(y_test, y_pred, target_names=label_encoder.classes_),
    )

    # --- Save model + label encoder together ---
    # Saving both in one file means load_model() always gets a consistent pair.
    # If you retrain with different classes, the encoder updates automatically.
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    joblib.dump({"model": clf, "label_encoder": label_encoder}, MODEL_PATH)
    logger.info(f"Model saved to {MODEL_PATH}")

    accuracy = report["accuracy"]
    return {
        "status":          "trained",
        "records_used":    len(records),
        "test_accuracy":   round(accuracy, 4),
        "model_path":      MODEL_PATH,
        "classes":         label_encoder.classes_.tolist(),
    }


# ---------------------------------------------------------------------------
# 3. LOAD + PREDICT
# ---------------------------------------------------------------------------

def load_model() -> dict:
    """
    Load the saved model and label encoder from MODEL_PATH.
    Called once at startup by main.py and cached — not reloaded per request.
    Raises FileNotFoundError if model.pkl does not exist yet.
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
) -> dict:
    """
    Run a single prediction using the loaded model bundle.
    Called by GET /predict on every request.

    model_bundle — the dict returned by load_model():
        {
          "model":         RandomForestClassifier,
          "label_encoder": LabelEncoder
        }

    Returns:
        {
          "location":          str,
          "day_of_week":       str,
          "hour":              int,
          "congestion_level":  str,   e.g. "High"
          "confidence":        float  e.g. 0.87
        }
    """
    clf           = model_bundle["model"]
    label_encoder = model_bundle["label_encoder"]

    # Build a single-row feature dict and encode it
    record = [{
        "hour":        hour,
        "day_of_week": day_of_week,
        "latitude":    latitude,
        "longitude":   longitude,
    }]
    X = encode_features(record)

    # Predict class and confidence (highest class probability)
    prediction_idx  = clf.predict(X)[0]
    probabilities   = clf.predict_proba(X)[0]
    confidence      = round(float(probabilities.max()), 4)
    congestion_label = label_encoder.inverse_transform([prediction_idx])[0]

    return {
        "location":         location_name,
        "day_of_week":      day_of_week,
        "hour":             hour,
        "congestion_level": congestion_label,
        "confidence":       confidence,
    }