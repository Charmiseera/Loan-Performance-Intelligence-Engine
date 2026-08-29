from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd


def build_asof_features_for_loan(
    loan_history: pd.DataFrame,
    asof_month: int,
) -> pd.Series:
    """
    Build temporal panel features strictly using history up to and including asof_month.
    Guarantees no future leakage (Principle II / FR-069).
    """
    # Filter strictly to history <= asof_month
    history = loan_history[loan_history["monthly_reporting_period"] <= asof_month].sort_values(
        by="monthly_reporting_period"
    )
    
    if history.empty:
        return pd.Series(dtype="float64")

    curr_row = history.iloc[-1]
    features: Dict[str, Any] = {}

    # As-of values
    features["current_actual_upb"] = float(curr_row.get("current_actual_upb", 0.0))
    features["current_interest_rate"] = float(curr_row.get("current_interest_rate", 0.0))
    features["delinquency_status_num"] = float(curr_row.get("delinq_num", curr_row.get("delinquency_status_num", 0.0)))
    features["remaining_months_to_maturity"] = float(curr_row.get("remaining_months_to_maturity", 0.0))
    features["derived_seasoning"] = float(len(history))

    # Lags
    if len(history) >= 2:
        features["delinq_lag_1"] = float(history.iloc[-2].get("delinq_num", history.iloc[-2].get("delinquency_status_num", 0.0)))
    else:
        features["delinq_lag_1"] = features["delinquency_status_num"]

    if len(history) >= 4:
        features["delinq_lag_3"] = float(history.iloc[-4].get("delinq_num", history.iloc[-4].get("delinquency_status_num", 0.0)))
    else:
        features["delinq_lag_3"] = features["delinquency_status_num"]

    # Rolling max delinquency
    h6 = history.tail(6)
    col_name = "delinq_num" if "delinq_num" in h6.columns else "delinquency_status_num"
    features["delinq_max_6m"] = float(h6[col_name].max()) if col_name in h6.columns else 0.0

    h12 = history.tail(12)
    features["delinq_max_12m"] = float(h12[col_name].max()) if col_name in h12.columns else 0.0

    # UPB Paydown ratio over past 6 months
    if len(history) >= 6 and history.iloc[-6].get("current_actual_upb", 0.0) > 0:
        upb_start = history.iloc[-6]["current_actual_upb"]
        features["upb_paydown_ratio_6m"] = float((upb_start - features["current_actual_upb"]) / upb_start)
    else:
        features["upb_paydown_ratio_6m"] = 0.0

    return pd.Series(features)
