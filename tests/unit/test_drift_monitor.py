import numpy as np
import pandas as pd
import pytest
from lpie.advanced.drift_monitor import compute_high_resolution_drift


def test_high_resolution_drift_monitor():
    np.random.seed(42)
    n = 500
    df_train = pd.DataFrame({
        "credit_score": np.random.normal(720, 40, size=n),
        "original_interest_rate": np.random.normal(4.5, 0.5, size=n),
        "channel": np.random.choice(["Retail", "Broker"], size=n),
    })
    df_score = pd.DataFrame({
        "credit_score": np.random.normal(722, 38, size=n),
        "original_interest_rate": np.random.normal(6.5, 0.8, size=n), # Drifted
        "channel": np.random.choice(["Retail", "Broker"], size=n),
    })

    drift_report = compute_high_resolution_drift(df_train, df_score)

    assert isinstance(drift_report, list)
    assert len(drift_report) == 3
    features_drift = {d["feature"]: d for d in drift_report}
    assert "credit_score" in features_drift
    assert "original_interest_rate" in features_drift
    assert features_drift["credit_score"]["drift_status"] in ("STABLE", "MODERATE_SHIFT")
    assert features_drift["original_interest_rate"]["drift_status"] == "SIGNIFICANT_SHIFT"
