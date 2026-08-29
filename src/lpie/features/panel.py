import numpy as np
import pandas as pd
from lpie.features.asof import build_asof_features_for_loan


def get_market_rate_proxy(period_series: pd.Series) -> pd.Series:
    """
    Vectorized macro mortgage benchmark rate (30-yr fixed proxy) by reporting period.
    Captures historical rate cycles (2006-2008 high, 2012-2021 low, 2022+ inflation hike)
    without lookahead bias.
    """
    year = (period_series // 100).astype(int)
    conditions = [
        year <= 2008,
        (year >= 2009) & (year <= 2012),
        (year >= 2013) & (year <= 2019),
        (year >= 2020) & (year <= 2021),
        year >= 2022,
    ]
    rates = [6.25, 4.60, 4.00, 3.10, 6.75]
    return pd.Series(np.select(conditions, rates, default=5.00), index=period_series.index)


def build_panel_feature_matrix(
    perf_df: pd.DataFrame,
    orig_features_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Build unified feature matrix combining static origination and as-of dynamic panel features.
    Includes rate spread incentive, 3m/6m balance velocities, acceleration, and delinquency velocity.
    Fully vectorized using groupby + shift/rolling.
    """
    df = perf_df.sort_values(by=["loan_id", "monthly_reporting_period"]).copy()

    # Ensure delinquency numeric column exists
    if "delinq_num" not in df.columns:
        from lpie.labels.outcomes import parse_delinquency_num
        df["delinq_num"] = df["current_delinquency_status"].apply(parse_delinquency_num)

    # Coerce nullable typed columns to float64
    for col in [
        "delinq_num", "current_actual_upb", "current_interest_rate",
        "remaining_months_to_maturity", "loan_age"
    ]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").astype("float64")

    g = df.groupby("loan_id", sort=False)

    # --- Lag features (within-loan, backward only) ---
    df["delinq_lag_1"] = g["delinq_num"].shift(1)
    df["delinq_lag_3"] = g["delinq_num"].shift(3)

    # --- Rolling max delinquency over trailing windows ---
    df["delinq_max_6m"] = g["delinq_num"].transform(
        lambda s: s.rolling(6, min_periods=1).max()
    )
    df["delinq_max_12m"] = g["delinq_num"].transform(
        lambda s: s.rolling(12, min_periods=1).max()
    )

    # --- Delinquency velocity (1m transition slope) ---
    df["delinq_velocity_1m"] = df["delinq_num"] - df["delinq_lag_1"].fillna(df["delinq_num"])

    # --- UPB paydown velocity (3m and 6m) ---
    upb_lag3 = g["current_actual_upb"].shift(2)
    upb_lag6 = g["current_actual_upb"].shift(5)

    df["upb_paydown_ratio_3m"] = np.where(
        upb_lag3.notna() & (upb_lag3 > 0),
        (upb_lag3 - df["current_actual_upb"]) / upb_lag3,
        0.0,
    )

    df["upb_paydown_ratio_6m"] = np.where(
        upb_lag6.notna() & (upb_lag6 > 0),
        (upb_lag6 - df["current_actual_upb"]) / upb_lag6,
        0.0,
    )

    # Paydown acceleration (surges right before complete prepayment payoff)
    df["upb_acceleration"] = df["upb_paydown_ratio_3m"] - (df["upb_paydown_ratio_6m"] / 2.0)

    # --- Refinancing / Prepayment Rate Spread Incentive ---
    market_proxy = get_market_rate_proxy(df["monthly_reporting_period"])
    curr_rate = df["current_interest_rate"].fillna(5.5)
    df["rate_spread_incentive"] = curr_rate - market_proxy

    # --- Loan seasoning ---
    df["derived_seasoning"] = g.cumcount() + 1

    # Fill NA in lags/rolls
    df["delinq_lag_1"] = df["delinq_lag_1"].fillna(df["delinq_num"])
    df["delinq_lag_3"] = df["delinq_lag_3"].fillna(df["delinq_num"])
    df["delinq_max_6m"] = df["delinq_max_6m"].fillna(0.0)
    df["delinq_max_12m"] = df["delinq_max_12m"].fillna(0.0)
    df["upb_paydown_ratio_3m"] = df["upb_paydown_ratio_3m"].fillna(0.0)
    df["upb_paydown_ratio_6m"] = df["upb_paydown_ratio_6m"].fillna(0.0)
    df["upb_acceleration"] = df["upb_acceleration"].fillna(0.0)

    # --- Select and rename final feature columns ---
    feat_cols = [
        "loan_id",
        "monthly_reporting_period",
        "delinq_num",
        "delinq_lag_1",
        "delinq_lag_3",
        "delinq_max_6m",
        "delinq_max_12m",
        "delinq_velocity_1m",
        "current_actual_upb",
        "upb_paydown_ratio_3m",
        "upb_paydown_ratio_6m",
        "upb_acceleration",
        "current_interest_rate",
        "rate_spread_incentive",
        "remaining_months_to_maturity",
        "derived_seasoning",
    ]
    for opt_col in ["servicer_name", "modification_flag", "loan_age"]:
        if opt_col in df.columns:
            feat_cols.append(opt_col)

    panel_feats_df = df[[c for c in feat_cols if c in df.columns]].rename(
        columns={"delinq_num": "delinquency_status_num"}
    )

    # Merge with static origination features
    full_df = panel_feats_df.merge(orig_features_df, on="loan_id", how="left")

    # Static interaction term
    if "original_dti" in full_df.columns and "original_ltv" in full_df.columns:
        full_df["dti_ltv_risk_product"] = (
            full_df["original_dti"].fillna(35.0) / 100.0
        ) * (full_df["original_ltv"].fillna(80.0) / 100.0)

    return full_df
