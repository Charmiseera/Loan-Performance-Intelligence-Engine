from typing import Any, Dict, Tuple
import numpy as np
import pandas as pd


def build_survival_dataset(
    perf_df: pd.DataFrame,
    max_duration_months: int = 120,
) -> pd.DataFrame:
    """
    Builds a right-censored time-to-event loan survival dataset (FR-037).
    Each loan receives:
    - duration_months: observable lifespan or loan age
    - event_type: 0 (censored/active), 1 (default/credit event), 2 (voluntary prepayment)
    """
    if perf_df.empty or "loan_id" not in perf_df.columns:
        return pd.DataFrame(columns=["loan_id", "duration_months", "event_type"])

    # Aggregate per loan
    records = []
    for loan_id, group in perf_df.groupby("loan_id"):
        duration = len(group)
        if "loan_age" in group.columns:
            valid_ages = pd.to_numeric(group["loan_age"], errors="coerce").dropna()
            if not valid_ages.empty:
                duration = int(valid_ages.max())

        duration = min(max_duration_months, max(1, duration))

        # Check termination or outcomes
        event = 0 # Censored / Active
        if "target_default_12m" in group.columns and group["target_default_12m"].max() == 1:
            event = 1 # Default
        elif "target_prepay_12m" in group.columns and group["target_prepay_12m"].max() == 1:
            event = 2 # Prepayment
        elif "zero_balance_code" in group.columns:
            zb = group["zero_balance_code"].dropna()
            if not zb.empty:
                last_zb = str(zb.iloc[-1]).strip()
                if last_zb in ("01", "1", "06", "6"):
                    event = 2 # Voluntary payoff
                elif last_zb in ("02", "03", "09", "2", "3", "9"):
                    event = 1 # Credit event / loss

        records.append({
            "loan_id": loan_id,
            "duration_months": duration,
            "event_type": event,
        })

    return pd.DataFrame(records)
