import numpy as np
import pandas as pd
import pytest
from lpie.advanced.fairness import audit_subgroup_fairness_and_calibration


def test_subgroup_fairness_parity_bounds():
    np.random.seed(42)
    n = 600
    df = pd.DataFrame({
        "credit_score": np.random.uniform(580, 800, size=n),
        "channel": np.random.choice(["Retail", "Broker", "Correspondent"], size=n),
        "prob_default_12m": np.random.uniform(0.01, 0.15, size=n),
        "target_default_12m": np.random.binomial(1, 0.05, size=n),
    })

    audit = audit_subgroup_fairness_and_calibration(
        df=df,
        prob_col="prob_default_12m",
        target_col="target_default_12m",
    )

    assert "credit_tier_parity" in audit
    assert "channel_fairness" in audit
    for tier, m in audit["credit_tier_parity"].items():
        assert m["sample_count"] > 0
        assert 0 <= m["brier_score"] <= 1.0
        assert 0 <= m["ece"] <= 1.0
