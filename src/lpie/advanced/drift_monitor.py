from typing import Any, Dict, List
import numpy as np
import pandas as pd
from scipy.stats import ks_2samp


def _calculate_psi(ref: np.ndarray, curr: np.ndarray, num_bins: int = 10) -> float:
    """Calculate Population Stability Index (PSI) with epsilon smoothing."""
    ref_clean = ref[~np.isnan(ref)]
    curr_clean = curr[~np.isnan(curr)]
    if len(ref_clean) < 10 or len(curr_clean) < 10:
        return 0.0

    quantiles = np.linspace(0, 100, num_bins + 1)
    bin_edges = np.percentile(ref_clean, quantiles)
    bin_edges = np.unique(bin_edges)
    if len(bin_edges) < 2:
        return 0.0

    ref_counts, _ = np.histogram(ref_clean, bins=bin_edges)
    curr_counts, _ = np.histogram(curr_clean, bins=bin_edges)

    ref_pct = np.maximum(ref_counts / len(ref_clean), 1e-4)
    curr_pct = np.maximum(curr_counts / len(curr_clean), 1e-4)

    psi = np.sum((curr_pct - ref_pct) * np.log(curr_pct / ref_pct))
    return float(psi)


def compute_high_resolution_drift(
    df_baseline: pd.DataFrame,
    df_target: pd.DataFrame,
    columns: List[str] = None,
) -> List[Dict[str, Any]]:
    """
    Computes Population Stability Index (PSI), Kolmogorov-Smirnov statistics,
    and alert tiers for all features across baseline vs target splits (FR-106).
    """
    cols_to_evaluate = columns or [
        c for c in df_baseline.columns
        if c in df_target.columns and c not in ("loan_id", "monthly_reporting_period")
    ]

    drift_records = []
    for col in cols_to_evaluate:
        s_base = df_baseline[col].dropna()
        s_targ = df_target[col].dropna()

        if s_base.empty or s_targ.empty:
            continue

        if pd.api.types.is_numeric_dtype(s_base):
            arr_base = s_base.to_numpy(dtype=float)
            arr_targ = s_targ.to_numpy(dtype=float)

            psi_val = _calculate_psi(arr_base, arr_targ)
            try:
                ks_res = ks_2samp(arr_base, arr_targ)
                ks_stat = float(ks_res.statistic)
                ks_pval = float(ks_res.pvalue)
            except Exception:
                ks_stat, ks_pval = 0.0, 1.0

            if psi_val < 0.10:
                status = "STABLE"
                alert = "GREEN"
            elif psi_val < 0.25:
                status = "MODERATE_SHIFT"
                alert = "YELLOW"
            else:
                status = "SIGNIFICANT_SHIFT"
                alert = "RED"

            drift_records.append({
                "feature": col,
                "data_type": "NUMERIC",
                "psi": round(psi_val, 4),
                "ks_statistic": round(ks_stat, 4),
                "ks_pvalue": round(ks_pval, 6),
                "drift_status": status,
                "alert_level": alert,
            })
        else:
            # Categorical distribution drift (frequency divergence)
            base_vc = s_base.value_counts(normalize=True)
            targ_vc = s_targ.value_counts(normalize=True)
            all_keys = list(set(base_vc.index).union(set(targ_vc.index)))

            p_base = np.array([base_vc.get(k, 1e-4) for k in all_keys])
            p_targ = np.array([targ_vc.get(k, 1e-4) for k in all_keys])
            psi_val = float(np.sum((p_targ - p_base) * np.log(p_targ / p_base)))

            status = "STABLE" if psi_val < 0.10 else ("MODERATE_SHIFT" if psi_val < 0.25 else "SIGNIFICANT_SHIFT")
            alert = "GREEN" if psi_val < 0.10 else ("YELLOW" if psi_val < 0.25 else "RED")

            drift_records.append({
                "feature": col,
                "data_type": "CATEGORICAL",
                "psi": round(psi_val, 4),
                "ks_statistic": 0.0,
                "ks_pvalue": 1.0,
                "drift_status": status,
                "alert_level": alert,
            })

    drift_records.sort(key=lambda x: x["psi"], reverse=True)
    return drift_records
