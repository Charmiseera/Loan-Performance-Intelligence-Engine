from typing import Any, Dict, List, Tuple
import numpy as np
import pandas as pd


def compute_cause_specific_hazards(
    survival_df: pd.DataFrame,
    max_time: int = 60,
) -> Dict[str, Any]:
    """
    Computes empirical cause-specific hazards and risk-set sizes at each time horizon t (FR-038, FR-040).
    Events:
    1 = Default
    2 = Prepayment
    0 = Censored
    """
    time_points = list(range(1, max_time + 1))
    n_total = len(survival_df)
    if n_total == 0:
        return {"time_points": [], "hazard_default": [], "hazard_prepay": [], "at_risk": []}

    hazard_default = []
    hazard_prepay = []
    at_risk_counts = []

    for t in time_points:
        # Loans observed at or beyond t
        at_risk = (survival_df["duration_months"] >= t).sum()
        at_risk_counts.append(int(at_risk))

        if at_risk > 0:
            events_def = ((survival_df["duration_months"] == t) & (survival_df["event_type"] == 1)).sum()
            events_prep = ((survival_df["duration_months"] == t) & (survival_df["event_type"] == 2)).sum()
            h_def = float(events_def / at_risk)
            h_prep = float(events_prep / at_risk)
        else:
            h_def = 0.0
            h_prep = 0.0

        hazard_default.append(round(h_def, 6))
        hazard_prepay.append(round(h_prep, 6))

    return {
        "time_points": time_points,
        "hazard_default": hazard_default,
        "hazard_prepay": hazard_prepay,
        "at_risk": at_risk_counts,
    }
