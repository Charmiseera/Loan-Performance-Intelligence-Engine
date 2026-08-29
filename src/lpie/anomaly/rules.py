from typing import Any, Dict, List, Tuple
import numpy as np
import pandas as pd


def evaluate_deterministic_rules(
    df: pd.DataFrame,
    rules_config: Dict[str, Any],
) -> Tuple[pd.Series, pd.DataFrame]:
    """
    Evaluate deterministic data integrity rules against panel records.
    Returns:
    - rule_violation_count: Series of violation counts per record
    - violation_details: DataFrame of boolean rule flags per record
    """
    rules = rules_config.get("rules", [])
    violation_df = pd.DataFrame(index=df.index)

    for r in rules:
        rule_id = r["id"]
        rule_name = r["name"]
        
        # Safe vectorized evaluations for defined rules
        if rule_name == "valid_maturity_sequence":
            if "maturity_date" in df.columns and "first_payment_date" in df.columns:
                violation = df["maturity_date"] <= df["first_payment_date"]
            else:
                violation = pd.Series(False, index=df.index)
        elif rule_name == "credit_score_range":
            if "credit_score" in df.columns:
                violation = df["credit_score"].notna() & ((df["credit_score"] < 300) | (df["credit_score"] > 850))
            else:
                violation = pd.Series(False, index=df.index)
        elif rule_name == "original_ltv_range":
            if "original_ltv" in df.columns:
                violation = df["original_ltv"].notna() & ((df["original_ltv"] <= 0) | (df["original_ltv"] > 200))
            else:
                violation = pd.Series(False, index=df.index)
        elif rule_name == "original_dti_range":
            if "original_dti" in df.columns:
                violation = df["original_dti"].notna() & ((df["original_dti"] <= 0) | (df["original_dti"] > 65))
            else:
                violation = pd.Series(False, index=df.index)
        elif rule_name == "upb_balance_cap":
            if "current_actual_upb" in df.columns and "original_upb" in df.columns:
                mod_flag = df["modification_flag"].fillna("") if "modification_flag" in df.columns else pd.Series("", index=df.index)
                violation = (df["current_actual_upb"] > df["original_upb"] * 1.05) & (~mod_flag.isin(["Y", "P"]))
            else:
                violation = pd.Series(False, index=df.index)
        elif rule_name == "interest_rate_bounds":
            rate_col = "current_interest_rate" if "current_interest_rate" in df.columns else "original_interest_rate"
            if rate_col in df.columns:
                violation = df[rate_col].notna() & ((df[rate_col] <= 0.1) | (df[rate_col] > 25.0))
            else:
                violation = pd.Series(False, index=df.index)
        elif rule_name == "delinquency_code_validity":
            if "current_delinquency_status" in df.columns:
                valid_codes = {"RA"} | {str(i).zfill(2) for i in range(100)}
                violation = df["current_delinquency_status"].notna() & (~df["current_delinquency_status"].isin(valid_codes))
            else:
                violation = pd.Series(False, index=df.index)
        else:
            violation = pd.Series(False, index=df.index)

        violation_df[rule_name] = violation.fillna(False)

    rule_violation_count = violation_df.sum(axis=1)
    return rule_violation_count, violation_df
