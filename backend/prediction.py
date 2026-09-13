"""Train and use a simple synthetic medicine demand prediction model."""

from pathlib import Path

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = PROJECT_ROOT / "data" / "historical_demand.csv"
MODEL_PATH = PROJECT_ROOT / "models" / "demand_prediction_model.joblib"

MODEL = None
LAST_TRAINING_RESULT = None


def load_data():
    """Load the existing historical demand data from the data folder."""
    data = pd.read_csv(DATA_PATH, parse_dates=["date"])
    required_columns = {
        "date",
        "hospital_id",
        "medicine_id",
        "medicine_name",
        "daily_demand",
    }
    missing_columns = required_columns.difference(data.columns)
    if missing_columns:
        raise ValueError(f"Missing required columns: {sorted(missing_columns)}")
    return data


def prepare_data(data):
    """Create simple calendar and identifier features for the model."""
    prepared = data.copy()
    prepared["day_of_week"] = prepared["date"].dt.dayofweek
    prepared["month"] = prepared["date"].dt.month
    prepared["day_of_month"] = prepared["date"].dt.day
    prepared["days_since_start"] = (
        prepared["date"] - prepared["date"].min()
    ).dt.days

    feature_columns = [
        "hospital_id",
        "medicine_id",
        "day_of_week",
        "month",
        "day_of_month",
        "days_since_start",
    ]
    return prepared[feature_columns], prepared["daily_demand"]


def build_model():
    """Build a pipeline that encodes IDs and trains a random forest regressor."""
    categorical_features = ["hospital_id", "medicine_id"]
    numeric_features = [
        "day_of_week",
        "month",
        "day_of_month",
        "days_since_start",
    ]

    preprocessing = ColumnTransformer(
        transformers=[
            (
                "identifiers",
                OneHotEncoder(handle_unknown="ignore"),
                categorical_features,
            ),
            ("calendar", "passthrough", numeric_features),
        ]
    )

    return Pipeline(
        steps=[
            ("preprocessing", preprocessing),
            (
                "regressor",
                RandomForestRegressor(
                    n_estimators=100,
                    random_state=42,
                    min_samples_leaf=1,
                ),
            ),
        ]
    )


def train_model():
    """Train, evaluate, and save the demand prediction model."""
    global MODEL, LAST_TRAINING_RESULT

    data = load_data()
    features, target = prepare_data(data)

    train_features, test_features, train_target, test_target = train_test_split(
        features,
        target,
        test_size=0.2,
        random_state=42,
    )

    model = build_model()
    model.fit(train_features, train_target)
    predictions = model.predict(test_features)

    evaluation = {
        "mae": mean_absolute_error(test_target, predictions),
        "rmse": mean_squared_error(test_target, predictions) ** 0.5,
        "r2": r2_score(test_target, predictions),
    }

    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    MODEL = model
    LAST_TRAINING_RESULT = evaluation

    print("Model evaluation on the synthetic test split:")
    print(f"MAE:  {evaluation['mae']:.2f}")
    print(f"RMSE: {evaluation['rmse']:.2f}")
    print(f"R2:   {evaluation['r2']:.2f}")
    print(f"Saved model to: {MODEL_PATH}")

    return evaluation


def _future_features(hospital_id, medicine_id):
    """Create features for the day immediately after the latest CSV date."""
    data = load_data()
    future_date = data["date"].max() + pd.Timedelta(days=1)
    return pd.DataFrame(
        [
            {
                "hospital_id": hospital_id,
                "medicine_id": medicine_id,
                "day_of_week": future_date.dayofweek,
                "month": future_date.month,
                "day_of_month": future_date.day,
                "days_since_start": (future_date - data["date"].min()).days,
            }
        ]
    )


def predict_demand(hospital_id, medicine_id):
    """Return the predicted demand for the next day in the CSV timeline."""
    global MODEL
    if MODEL is None:
        train_model()

    prediction = MODEL.predict(_future_features(hospital_id, medicine_id))[0]
    return max(0.0, float(prediction))


if __name__ == "__main__":
    train_model()