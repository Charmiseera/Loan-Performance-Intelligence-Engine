import numpy as np
import pandas as pd
from lpie.data.drift import calculate_psi, compute_population_drift


def test_calculate_psi_stable():
    np.random.seed(42)
    dist1 = np.random.normal(700, 50, 1000)
    dist2 = np.random.normal(700, 50, 1000)
    psi = calculate_psi(dist1, dist2)
    assert psi < 0.10  # Stable


def test_calculate_psi_shifted():
    np.random.seed(42)
    dist1 = np.random.normal(700, 50, 1000)
    dist2 = np.random.normal(600, 50, 1000)
    psi = calculate_psi(dist1, dist2)
    assert psi > 0.25  # Significant drift


def test_compute_population_drift():
    np.random.seed(42)
    df_train = pd.DataFrame({
        "credit_score": np.random.normal(720, 40, 500),
        "dti": np.random.normal(35, 8, 500),
    })
    df_score = pd.DataFrame({
        "credit_score": np.random.normal(650, 40, 500), # shifted
        "dti": np.random.normal(35, 8, 500),            # identical
    })

    drift_res = compute_population_drift(df_train, df_score)
    assert len(drift_res) == 2
    # credit_score should have highest PSI and appear first
    assert drift_res[0]["feature"] == "credit_score"
    assert drift_res[0]["psi"] > drift_res[1]["psi"]
