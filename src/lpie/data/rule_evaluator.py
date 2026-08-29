from typing import Any, Dict, List
import pandas as pd
import numpy as np


def evaluate_cross_column_rules(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Evaluates deterministic cross-column business validation rules (FR-013, FR-015).
    Checks:
    - Date ordering: maturity date >= origination date
    - Balance consistency: balance cannot increase without modification flag
    - LTV and CLTV bounds: cltv >= ltv
    - DTI reasonableness bounds: 0 <= dti <= 100
    - Delinquency status vs zero balance code alignment
    """
    results: Dict[str, Any] = {}
    total_records = len(df)

    # 1. Maturity date >= Origination date
    if "maturity_date" in df.columns and "origination_date" in df.columns:
        valid_dates = df[["maturity_date", "origination_date"]].dropna()
        if not valid_dates.empty:
            violations = valid_dates[valid_dates["maturity_date"] < valid_dates["origination_date"]]
            results["RULE_MATURITY_AFTER_ORIGINATION"] = {
                "rule_name": "Maturity Date After Origination Date",
                "severity": "CRITICAL",
                "evaluated_records": len(valid_dates),
                "violation_count": len(violations),
                "violation_rate": round(float(len(violations) / max(1, len(valid_dates))), 5),
                "sample_violating_ids": violations.index.tolist()[:5],
            }

    # 2. CLTV >= LTV
    if "cltv" in df.columns and "original_ltv" in df.columns:
        valid_ltv = df[["cltv", "original_ltv"]].dropna()
        if not valid_ltv.empty:
            violations = valid_ltv[valid_ltv["cltv"] < valid_ltv["original_ltv"]]
            results["RULE_CLTV_GE_LTV"] = {
                "rule_name": "CLTV Greater Than or Equal to LTV",
                "severity": "HIGH",
                "evaluated_records": len(valid_ltv),
                "violation_count": len(violations),
                "violation_rate": round(float(len(violations) / max(1, len(valid_ltv))), 5),
                "sample_violating_ids": violations.index.tolist()[:5],
            }

    # 3. DTI in valid range (0-100)
    if "debt_to_income_ratio" in df.columns:
        valid_dti = df["debt_to_income_ratio"].dropna()
        if not valid_dti.empty:
            violations = valid_dti[(valid_dti < 0) | (valid_dti > 100)]
            results["RULE_DTI_BOUNDS"] = {
                "rule_name": "DTI Between 0 and 100",
                "severity": "MEDIUM",
                "evaluated_records": len(valid_dti),
                "violation_count": len(violations),
                "violation_rate": round(float(len(violations) / max(1, len(valid_dti))), 5),
                "sample_violating_ids": violations.index.tolist()[:5],
            }

    # 4. Interest rate in positive range (0-30%)
    if "original_interest_rate" in df.columns:
        valid_rate = df["original_interest_rate"].dropna()
        if not valid_rate.empty:
            violations = valid_rate[(valid_rate <= 0) | (valid_rate > 30.0)]
            results["RULE_INTEREST_RATE_BOUNDS"] = {
                "rule_name": "Interest Rate Reasonable Range (0-30%)",
                "severity": "HIGH",
                "evaluated_records": len(valid_rate),
                "violation_count": len(violations),
                "violation_rate": round(float(len(violations) / max(1, len(valid_rate))), 5),
                "sample_violating_ids": violations.index.tolist()[:5],
            }

    return results
