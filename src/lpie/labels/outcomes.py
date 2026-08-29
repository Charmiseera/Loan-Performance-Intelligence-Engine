from typing import Any, List
import numpy as np
import pandas as pd
from lpie.labels.termination import TerminationClass, classify_zero_balance_code


def parse_delinquency_num(val: Any) -> float:
    """Parse delinquency status into integer months delinquent, or 999 for REO (RA)."""
    if pd.isna(val) or val is None:
        return 0.0
    s = str(val).strip()
    if s == "RA":
        return 12.0  # REO status treated as severe delinquency
    try:
        return float(int(s))
    except ValueError:
        return 0.0


def compute_horizon_targets(perf_df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute forward-looking outcome targets for all loan-month observation rows.
    Requires perf_df sorted by ['loan_id', 'monthly_reporting_period'].
    
    Constructs:
    - target_deterioration_3m (binary 0/1)
    - target_deterioration_6m (binary 0/1)
    - target_default_12m (binary 0/1)
    - target_prepay_12m (binary 0/1)
    - target_next_state (categorical string)
    """
    df = perf_df.sort_values(by=["loan_id", "monthly_reporting_period"]).copy()
    
    # Parse delinquency status
    df["delinq_num"] = df["current_delinquency_status"].apply(parse_delinquency_num)
    df["term_class"] = df["zero_balance_code"].apply(classify_zero_balance_code)
    
    # Output containers
    target_det_3m = []
    target_det_6m = []
    target_def_12m = []
    target_prep_12m = []
    target_next_st = []
    
    # Group by loan to resolve future horizons
    for _, group in df.groupby("loan_id", sort=False):
        n = len(group)
        delinqs = group["delinq_num"].values
        term_classes = group["term_class"].values
        
        for i in range(n):
            curr_delinq = delinqs[i]
            
            # Next state (month i + 1)
            if i + 1 < n:
                next_delinq = delinqs[i + 1]
                next_term = term_classes[i + 1]
                if next_term == TerminationClass.PREPAYMENT:
                    st = "PREPAID"
                elif next_term == TerminationClass.CREDIT_EVENT or next_delinq >= 3:
                    st = "90_PLUS_DELINQUENT"
                elif next_delinq == 2:
                    st = "60_DAYS_DELINQUENT"
                elif next_delinq == 1:
                    st = "30_DAYS_DELINQUENT"
                else:
                    st = "CURRENT"
            else:
                # Terminal record of observation
                curr_term = term_classes[i]
                if curr_term == TerminationClass.PREPAYMENT:
                    st = "PREPAID"
                elif curr_term == TerminationClass.CREDIT_EVENT or curr_delinq >= 3:
                    st = "90_PLUS_DELINQUENT"
                elif curr_delinq == 2:
                    st = "60_DAYS_DELINQUENT"
                elif curr_delinq == 1:
                    st = "30_DAYS_DELINQUENT"
                else:
                    st = "CURRENT"
            target_next_st.append(st)
            
            # 3-month deterioration window
            w3_delinq = delinqs[i + 1 : min(n, i + 4)]
            w3_term = term_classes[i + 1 : min(n, i + 4)]
            is_det_3m = 0
            if len(w3_delinq) > 0:
                if any(d > curr_delinq or d >= 2 for d in w3_delinq) or any(t == TerminationClass.CREDIT_EVENT for t in w3_term):
                    is_det_3m = 1
            target_det_3m.append(is_det_3m)
            
            # 6-month deterioration window
            w6_delinq = delinqs[i + 1 : min(n, i + 7)]
            w6_term = term_classes[i + 1 : min(n, i + 7)]
            is_det_6m = 0
            if len(w6_delinq) > 0:
                if any(d > curr_delinq or d >= 2 for d in w6_delinq) or any(t == TerminationClass.CREDIT_EVENT for t in w6_term):
                    is_det_6m = 1
            target_det_6m.append(is_det_6m)
            
            # 12-month default window
            w12_delinq = delinqs[i + 1 : min(n, i + 13)]
            w12_term = term_classes[i + 1 : min(n, i + 13)]
            is_def_12m = 0
            if len(w12_delinq) > 0:
                if any(t == TerminationClass.CREDIT_EVENT for t in w12_term) or any(d >= 3 for d in w12_delinq):
                    is_def_12m = 1
            target_def_12m.append(is_def_12m)
            
            # 12-month prepay window
            is_prep_12m = 0
            if len(w12_term) > 0:
                if any(t == TerminationClass.PREPAYMENT for t in w12_term):
                    is_prep_12m = 1
            target_prep_12m.append(is_prep_12m)
            
    df["target_deterioration_3m"] = target_det_3m
    df["target_deterioration_6m"] = target_det_6m
    df["target_default_12m"] = target_def_12m
    df["target_prepay_12m"] = target_prep_12m
    df["target_next_state"] = target_next_st
    
    return df
