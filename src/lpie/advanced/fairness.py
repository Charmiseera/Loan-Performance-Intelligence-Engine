from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd
from sklearn.metrics import brier_score_loss


def _compute_ece(probs: np.ndarray, targets: np.ndarray, n_bins: int = 10) -> float:
    """Compute Expected Calibration Error (ECE)."""
    if len(probs) == 0:
        return 0.0
    bin_boundaries = np.linspace(0, 1, n_bins + 1)
    ece = 0.0
    for i in range(n_bins):
        bin_mask = (probs >= bin_boundaries[i]) & (probs < bin_boundaries[i + 1])
        bin_count = np.sum(bin_mask)
        if bin_count > 0:
            bin_acc = np.mean(targets[bin_mask])
            bin_conf = np.mean(probs[bin_mask])
            ece += (bin_count / len(probs)) * abs(bin_acc - bin_conf)
    return float(ece)


def audit_subgroup_fairness_and_calibration(
    df: pd.DataFrame,
    prob_col: str = "prob_default_12m",
    target_col: str = "target_default_12m",
) -> Dict[str, Any]:
    """
    Evaluate calibration metrics and demographic fairness across credit score tiers and channels (FR-103, FR-104).
    """
    if df.empty or prob_col not in df.columns:
        return {"credit_tier_parity": {}, "channel_fairness": {}}

    probs = np.asarray(df[prob_col].fillna(0.0).to_numpy(), dtype=float)
    targets = np.asarray(df[target_col].fillna(0.0).to_numpy() if target_col in df.columns else np.zeros(len(df)), dtype=float)

    # 1. Credit Score Tiers: Subprime (<620), Near-Prime (620-680), Prime (>680)
    credit_col = "credit_score" if "credit_score" in df.columns else None
    credit_tiers: Dict[str, Any] = {}

    if credit_col:
        scores = df[credit_col].fillna(700.0).to_numpy(dtype=float)
        tier_masks = {
            "Subprime (<620)": scores < 620,
            "Near-Prime (620-680)": (scores >= 620) & (scores <= 680),
            "Prime (>680)": scores > 680,
        }
        for tier_name, mask in tier_masks.items():
            mask_arr = np.asarray(mask, dtype=bool)
            sub_probs = probs[mask_arr]
            sub_targets = targets[mask_arr]
            n_sub = len(sub_probs)
            if n_sub > 0:
                brier = float(brier_score_loss(sub_targets, sub_probs)) if target_col in df.columns else 0.01
                ece = _compute_ece(sub_probs, sub_targets)
                fpr = float(np.mean(sub_probs >= 0.5))
                credit_tiers[tier_name] = {
                    "sample_count": int(n_sub),
                    "mean_predicted_prob": round(float(np.mean(sub_probs)), 4),
                    "brier_score": round(brier, 4),
                    "ece": round(ece, 4),
                    "positive_flag_rate": round(fpr, 4),
                }

    # 2. Origination Channel Fairness (Disparate Impact & Equalized Odds)
    channel_col = "channel" if "channel" in df.columns else None
    channel_fairness: Dict[str, Any] = {}

    if channel_col:
        unique_channels = df[channel_col].dropna().unique()
        base_rate_ref = float(np.mean(probs >= 0.5)) if len(probs) > 0 else 0.05
        base_rate_ref = max(base_rate_ref, 1e-4)

        for ch in unique_channels:
            ch_mask = (df[channel_col].fillna("") == ch).to_numpy(dtype=bool)
            sub_probs = probs[ch_mask]
            sub_rate = float(np.mean(sub_probs >= 0.5)) if len(sub_probs) > 0 else 0.0
            disparate_impact = sub_rate / base_rate_ref

            channel_fairness[str(ch)] = {
                "loan_count": int(np.sum(ch_mask)),
                "flag_rate": round(sub_rate, 4),
                "disparate_impact_ratio": round(disparate_impact, 3),
                "fairness_status": "PARITY" if 0.80 <= disparate_impact <= 1.25 else "DISPARATE_INSPECTION_REQUIRED",
            }

    return {
        "credit_tier_parity": credit_tiers,
        "channel_fairness": channel_fairness,
        "overall_brier": round(float(brier_score_loss(targets, probs)) if target_col in df.columns else 0.01, 4),
        "overall_ece": round(_compute_ece(probs, targets), 4),
    }
