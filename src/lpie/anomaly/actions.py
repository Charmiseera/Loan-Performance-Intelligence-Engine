from typing import List
import pandas as pd


def determine_recommended_action(
    exception_required: pd.Series,
    exception_type: pd.Series,
    prob_default_12m: pd.Series,
    prob_prepay_12m: pd.Series,
) -> pd.Series:
    """
    Deterministic decision table for reviewer recommended actions (Constitution Principle I).
    Actions:
    - DATA_INTEGRITY_AUDIT: for rule violations and integrity exceptions
    - SERVICER_OUTREACH: for high default probability or acceleration
    - REFINANCE_RETENTION: for high prepayment probability
    - MANUAL_REVIEW: for extreme statistical outliers
    - MONITOR: for normal performing loans
    """
    actions: List[str] = []
    
    for exc_req, exc_tp, p_def, p_prep in zip(
        exception_required, exception_type, prob_default_12m, prob_prepay_12m
    ):
        if exc_tp in ("MULTI_RULE_VIOLATION", "INTEGRITY_EXCEPTION"):
            actions.append("DATA_INTEGRITY_AUDIT")
        elif exc_tp == "EXTREME_STATISTICAL_OUTLIER":
            actions.append("MANUAL_REVIEW")
        elif p_def >= 0.35 or exc_tp == "DELINQUENCY_ACCELERATION":
            actions.append("SERVICER_OUTREACH")
        elif p_prep >= 0.50:
            actions.append("REFINANCE_RETENTION")
        elif exc_req:
            actions.append("FLAG_FOR_REVIEW")
        else:
            actions.append("MONITOR")

    return pd.Series(actions, index=exception_required.index)
