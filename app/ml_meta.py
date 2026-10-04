from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, log_loss, roc_auc_score
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline

FEATURE_COLUMNS = [
    "atr_percentile",
    "adx",
    "ema_slope_atr",
    "bb_width",
    "rsi",
    "vwap_distance_atr",
    "recent_return",
    "spread_percentile",
    "hour_utc",
    "news_proximity_minutes",
]


@dataclass(frozen=True)
class MetaModelMetrics:
    train_rows: int
    validation_rows: int
    accuracy: float
    roc_auc: float | None
    log_loss: float

    def to_dict(self) -> dict:
        return asdict(self)


def validate_dataset(frame: pd.DataFrame) -> pd.DataFrame:
    missing = [c for c in FEATURE_COLUMNS + ["success"] if c not in frame.columns]
    if missing:
        raise ValueError(f"Missing ML columns: {missing}")

    clean = frame[FEATURE_COLUMNS + ["success"]].replace([np.inf, -np.inf], np.nan).dropna()
    if len(clean) < 200:
        raise ValueError("At least 200 clean labeled rows are required for ML training")
    if clean["success"].nunique() < 2:
        raise ValueError("ML labels must contain both successful and unsuccessful trades")
    return clean


def train_meta_model(
    frame: pd.DataFrame,
    *,
    validation_fraction: float = 0.25,
) -> tuple[Pipeline, MetaModelMetrics]:
    clean = validate_dataset(frame)
    split = int(len(clean) * (1.0 - validation_fraction))
    if split < 100 or len(clean) - split < 50:
        raise ValueError("Chronological train/validation split is too small")

    train = clean.iloc[:split]
    validation = clean.iloc[split:]

    model = Pipeline(
        steps=[
            ("scale", StandardScaler()),
            ("clf", LogisticRegression(max_iter=2000, class_weight="balanced")),
        ]
    )
    model.fit(train[FEATURE_COLUMNS], train["success"])

    probabilities = model.predict_proba(validation[FEATURE_COLUMNS])[:, 1]
    predictions = (probabilities >= 0.5).astype(int)

    auc = None
    if validation["success"].nunique() == 2:
        auc = float(roc_auc_score(validation["success"], probabilities))

    metrics = MetaModelMetrics(
        train_rows=len(train),
        validation_rows=len(validation),
        accuracy=float(accuracy_score(validation["success"], predictions)),
        roc_auc=auc,
        log_loss=float(log_loss(validation["success"], probabilities, labels=[0, 1])),
    )
    return model, metrics


def save_model(model: Pipeline, path: str | Path) -> str:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, target)
    return str(target)


def load_model(path: str | Path) -> Pipeline:
    return joblib.load(path)


def predict_success_probability(model: Pipeline, features: dict) -> float:
    row = pd.DataFrame([{name: features[name] for name in FEATURE_COLUMNS}])
    return float(model.predict_proba(row)[0, 1])
