import pandas as pd
from lpie.survival.dataset import build_survival_dataset
from lpie.survival.cause_specific import compute_cause_specific_hazards


def test_survival_dataset_and_hazard():
    perf_df = pd.DataFrame({
        "loan_id": ["L1", "L1", "L2", "L2", "L3"],
        "loan_age": [1, 2, 1, 2, 1],
        "target_default_12m": [0, 1, 0, 0, 0],
        "target_prepay_12m": [0, 0, 0, 1, 0],
    })

    surv_df = build_survival_dataset(perf_df)
    assert len(surv_df) == 3
    assert set(surv_df["event_type"].unique()).issubset({0, 1, 2})

    hazards = compute_cause_specific_hazards(surv_df, max_time=3)
    assert len(hazards["time_points"]) == 3
    assert len(hazards["hazard_default"]) == 3
    assert len(hazards["hazard_prepay"]) == 3
    assert hazards["at_risk"][0] == 3
