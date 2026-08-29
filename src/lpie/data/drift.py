from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd
from scipy import stats


def calculate_psi(
    expected: np.ndarray,
    actual: np.ndarray,
    num_buckets: int = 10,
    epsilon: float = 1e-4,
) -> float:
    """
    Computes Population Stability Index (PSI) between reference (expected/train)
    and target (actual/scoring) distributions (FR-016).
    """
    expected = expected[~np.isnan(expected)]
    actual = actual[~np.isnan(actual)]

    if len(expected) == 0 or len(actual) == 0:
        return 0.0

    # Determine quantile bins on expected distribution
    quantiles = np.linspace(0, 100, num_buckets + 1)
    try:
        bin_edges = np.percentile(expected, quantiles)
        bin_edges = np.unique(bin_edges)
        if len(bin_edges) < 2:
            return 0.0
    except Exception:
        return 0.0

    # Ensure min and max bounds enclose both
    bin_edges[0] = min(bin_edges[0], actual.min(), expected.min()) - 1e-5
    bin_edges[-1] = max(bin_edges[-1], actual.max(), expected.max()) + 1e-5

    expected_counts, _ = np.histogram(expected, bins=bin_edges)
    actual_counts, _ = np.histogram(actual, bins=bin_edges)

    expected_pct = expected_counts / max(1, len(expected))
    actual_pct = actual_counts / max(1, len(actual))

    # Apply smoothing epsilon
    expected_pct = np.where(expected_pct == 0, epsilon, expected_pct)
    actual_pct = np.where(actual_pct == 0, epsilon, actual_pct)

    psi_val = np.sum((actual_pct - expected_pct) * np.log(actual_pct / expected_pct))
    return float(max(0.0, psi_val))


def compute_population_drift(
    train_df: pd.DataFrame,
    scoring_df: pd.DataFrame,
    feature_cols: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """
    Quantifies population shift between training and scoring windows per field,
    and ranks fields by shift magnitude (FR-016, SC-015).
    """
    if feature_cols is None:
        numeric_cols = train_df.select_dtypes(include=[np.number]).columns.tolist()
        feature_cols = [c for c in numeric_cols if c in scoring_df.columns and not c.startswith("target_")]

    drift_results: List[Dict[str, Any]] = []

    for col in feature_cols:
        train_vals = pd.to_numeric(train_df[col], errors="coerce").dropna().values
        score_vals = pd.to_numeric(scoring_df[col], errors="coerce").dropna().values

        if len(train_vals) < 10 or len(score_vals) < 10:
            continue

        psi = calculate_psi(train_vals, score_vals)

        # Kolmogorov-Smirnov 2-sample test
        ks_res = stats.ks_2samp(train_vals, score_vals)
        ks_stat = float(ks_res.statistic)
        ks_pvalue = float(ks_res.pvalue)

        # Categorize drift severity
        if psi > 0.25:
            drift_status = "SIGNIFICANT_DRIFT"
        elif psi > 0.10:
            drift_status = "MODERATE_DRIFT"
        else:
            drift_status = "STABLE"

        drift_results.append({
            "feature": col,
            "psi": round(psi, 5),
            "ks_statistic": round(ks_stat, 5),
            "ks_pvalue": round(ks_pvalue, 6),
            "drift_status": drift_status,
            "train_mean": round(float(np.mean(train_vals)), 4),
            "scoring_mean": round(float(np.mean(score_vals)), 4),
            "train_count": len(train_vals),
            "scoring_count": len(score_vals),
        })

    # Rank by PSI magnitude descending (FR-016)
    drift_results.sort(key=lambda x: x["psi"], reverse=True)
    return drift_results
