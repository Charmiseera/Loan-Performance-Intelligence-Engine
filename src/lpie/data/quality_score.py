from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd


def compute_record_quality_scores(
    df: pd.DataFrame,
    critical_fields: Optional[List[str]] = None,
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Assigns every record an inspectable multi-component data quality score (0.0 - 100.0) (FR-017, SC-016),
    and derives the batch-level quality score (FR-018).

    Components:
    1. Completeness Score (40 pts): Penalty for missing required/critical fields.
    2. Validity Score (30 pts): Penalty for out-of-bounds sentinels or negative terms.
    3. Consistency Score (30 pts): Penalty for cross-column logic violations.
    """
    if critical_fields is None:
        critical_fields = [
            "loan_id", "origination_date", "original_upb", "original_interest_rate",
            "original_loan_term", "original_ltv", "debt_to_income_ratio", "borrower_credit_score"
        ]

    n_rows = len(df)
    if n_rows == 0:
        return pd.DataFrame(), {"batch_quality_score": 0.0}

    # 1. Completeness component (0 - 40)
    avail_critical = [c for c in critical_fields if c in df.columns]
    if avail_critical:
        missing_count = df[avail_critical].isna().sum(axis=1)
        completeness_score = (1.0 - (missing_count / len(avail_critical))) * 40.0
    else:
        completeness_score = pd.Series(40.0, index=df.index)

    # 2. Validity component (0 - 30)
    validity_score = pd.Series(30.0, index=df.index)
    if "debt_to_income_ratio" in df.columns:
        dti = pd.to_numeric(df["debt_to_income_ratio"], errors="coerce")
        validity_score -= np.where((dti < 0) | (dti > 100), 10.0, 0.0)

    if "original_interest_rate" in df.columns:
        rate = pd.to_numeric(df["original_interest_rate"], errors="coerce")
        validity_score -= np.where((rate <= 0) | (rate > 25.0), 10.0, 0.0)

    validity_score = validity_score.clip(lower=0.0, upper=30.0)

    # 3. Consistency component (0 - 30)
    consistency_score = pd.Series(30.0, index=df.index)
    if "cltv" in df.columns and "original_ltv" in df.columns:
        cltv = pd.to_numeric(df["cltv"], errors="coerce")
        ltv = pd.to_numeric(df["original_ltv"], errors="coerce")
        consistency_score -= np.where(cltv < ltv, 15.0, 0.0)

    consistency_score = consistency_score.clip(lower=0.0, upper=30.0)

    total_quality_score = (completeness_score + validity_score + consistency_score).round(2)

    quality_df = pd.DataFrame({
        "completeness_score": completeness_score.round(2),
        "validity_score": validity_score.round(2),
        "consistency_score": consistency_score.round(2),
        "total_quality_score": total_quality_score,
    }, index=df.index)

    batch_summary = {
        "total_records_scored": n_rows,
        "batch_mean_quality_score": round(float(total_quality_score.mean()), 2),
        "batch_median_quality_score": round(float(total_quality_score.median()), 2),
        "high_quality_record_share": round(float((total_quality_score >= 80.0).mean()), 4),
        "low_quality_record_share": round(float((total_quality_score < 50.0).mean()), 4),
        "mean_completeness": round(float(completeness_score.mean()), 2),
        "mean_validity": round(float(validity_score.mean()), 2),
        "mean_consistency": round(float(consistency_score.mean()), 2),
    }

    return quality_df, batch_summary
