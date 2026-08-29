import numpy as np
import pandas as pd
import pytest
from lpie.data.sentinels import apply_sentinel_policy, extract_sentinel_audit


def test_apply_sentinel_policy_numeric_and_string():
    df = pd.DataFrame({
        "credit_score": [720.0, 9999.0, 650.0],
        "original_dti": [35.0, 999.0, 28.0],
        "mi_percentage": [0.0, 999.0, 25.0],  # 0.0 is legitimate No MI, 999 is missing
        "current_delinquency_status": ["00", "99", "RA"],  # 99 is 99 months delinquent, NOT sentinel!
        "occupancy_status": ["P", "9", "I"],
    })
    
    sentinel_map = {
        "credit_score": [9999, 9999.0],
        "original_dti": [999, 999.0],
        "mi_percentage": [999, 999.0],
        "occupancy_status": ["9"],
    }
    
    cleaned_df, audit = apply_sentinel_policy(df, sentinel_map)
    
    assert pd.isna(cleaned_df["credit_score"].iloc[1])
    assert cleaned_df["credit_score"].iloc[0] == 720.0
    
    assert pd.isna(cleaned_df["original_dti"].iloc[1])
    assert pd.isna(cleaned_df["occupancy_status"].iloc[1])
    
    # 0.0 for MI is valid (No MI)
    assert cleaned_df["mi_percentage"].iloc[0] == 0.0
    assert pd.isna(cleaned_df["mi_percentage"].iloc[1])
    
    # Delinquency status 99 must remain intact!
    assert cleaned_df["current_delinquency_status"].iloc[1] == "99"
    
    assert audit["credit_score"]["replaced_count"] == 1
    assert audit["original_dti"]["replaced_count"] == 1
