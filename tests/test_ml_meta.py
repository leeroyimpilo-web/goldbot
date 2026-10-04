import numpy as np
import pandas as pd

from app.ml_meta import FEATURE_COLUMNS, train_meta_model


def test_meta_model_trains_chronologically():
    n = 240
    rng = np.random.default_rng(7)
    data = {name: rng.normal(size=n) for name in FEATURE_COLUMNS}
    data["success"] = np.array(([0, 1] * (n // 2)), dtype=int)
    frame = pd.DataFrame(data)
    model, metrics = train_meta_model(frame)
    assert metrics.train_rows > metrics.validation_rows
    assert 0 <= metrics.accuracy <= 1
    assert hasattr(model, "predict_proba")
