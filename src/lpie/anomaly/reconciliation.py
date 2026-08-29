from typing import Any, Dict, List
import pandas as pd
import numpy as np


def generate_reconciliation_fixture(
    scoring_records: pd.DataFrame,
    sample_size: int = 100,
    seed: int = 42,
) -> pd.DataFrame:
    """
    Constructs a synthetic second-source servicer conflict fixture (FR-043, SC-026).
    All records are explicitly tagged as CONSTRUCTED_FIXTURE (Principle V / SC-026).

    Simulates servicer-reported discrepancies:
    - Discrepant current UPB (e.g. +/- 5% due to timing lag)
    - Discrepant delinquency status (e.g. 30 vs 60 days delinquent)
    - Conflicting modification status
    """
    if scoring_records.empty:
        return pd.DataFrame()

    rng = np.random.default_rng(seed)
    n = min(sample_size, len(scoring_records))
    sampled_indices = rng.choice(len(scoring_records), size=n, replace=False)
    sub = scoring_records.iloc[sampled_indices].copy()

    # Generate synthetic second source columns
    source_b_upb = []
    source_b_delinq = []
    discrepancy_types = []

    for _, row in sub.iterrows():
        orig_upb = float(row.get("current_actual_upb", 200000.0) if "current_actual_upb" in row else 200000.0)
        disc_choice = rng.choice(["BALANCE_DISCREPANCY", "STATUS_DISCREPANCY", "PAYMENT_TIMING"])

        if disc_choice == "BALANCE_DISCREPANCY":
            b_upb = round(orig_upb * (1.0 + rng.uniform(-0.08, 0.08)), 2)
            b_del = row.get("current_loan_delinquency_status", "0")
        elif disc_choice == "STATUS_DISCREPANCY":
            b_upb = orig_upb
            b_del = "1" if str(row.get("current_loan_delinquency_status", "0")) == "0" else "0"
        else:
            b_upb = round(orig_upb - rng.uniform(500, 2500), 2)
            b_del = row.get("current_loan_delinquency_status", "0")

        source_b_upb.append(b_upb)
        source_b_delinq.append(str(b_del))
        discrepancy_types.append(disc_choice)

    loan_ids = sub["loan_id"].astype(str) if "loan_id" in sub.columns else pd.Series([f"LOAN_{i:04d}" for i in range(len(sub))], index=sub.index)
    rep_months = sub["monthly_reporting_period"].astype(int) if "monthly_reporting_period" in sub.columns else pd.Series([202401] * len(sub), index=sub.index)
    source_a_upb = sub["current_actual_upb"] if "current_actual_upb" in sub.columns else pd.Series([200000.0] * len(sub), index=sub.index)
    source_a_del = sub["current_loan_delinquency_status"].astype(str) if "current_loan_delinquency_status" in sub.columns else pd.Series(["0"] * len(sub), index=sub.index)

    fixture_df = pd.DataFrame({
        "loan_id": loan_ids,
        "reporting_month": rep_months,
        "source_a_servicer_upb": source_a_upb,
        "source_b_master_servicer_upb": source_b_upb,
        "source_a_delinquency_status": source_a_del,
        "source_b_delinquency_status": source_b_delinq,
        "discrepancy_type": discrepancy_types,
        "fixture_provenance": "CONSTRUCTED_SYNTHETIC_FIXTURE_DO_NOT_TREAT_AS_OBSERVED",
    })

    return fixture_df
