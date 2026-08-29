from typing import List
import numpy as np
import pandas as pd


def prepare_static_origination_features(orig_df: pd.DataFrame) -> pd.DataFrame:
    """
    Extract and format static origination features.
    """
    df = orig_df.copy()
    static_cols = [
        "loan_id",
        "credit_score",
        "original_upb",
        "original_interest_rate",
        "original_ltv",
        "original_cltv",
        "original_dti",
        "original_loan_term",
        "borrower_count",
        "occupancy_status",
        "channel",
        "loan_purpose",
        "property_type",
        "property_state",
    ]
    avail_cols = [c for c in static_cols if c in df.columns]
    return df[avail_cols]
