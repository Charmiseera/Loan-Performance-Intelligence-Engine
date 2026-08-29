from typing import Any, Dict, Optional, Tuple
import numpy as np
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    log_loss,
    precision_recall_curve,
    roc_auc_score,
)


def compute_expected_calibration_error(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    n_bins: int = 10,
) -> float:
    """Compute Expected Calibration Error (ECE) across probability bins."""
    bin_boundaries = np.linspace(0, 1, n_bins + 1)
    ece = 0.0
    n = len(y_true)
    if n == 0:
        return 0.0

    for i in range(n_bins):
        bin_lower = bin_boundaries[i]
        bin_upper = bin_boundaries[i + 1]
        
        # Include upper boundary in last bin
        if i == n_bins - 1:
            in_bin = (y_prob >= bin_lower) & (y_prob <= bin_upper)
        else:
            in_bin = (y_prob >= bin_lower) & (y_prob < bin_upper)

        bin_count = np.sum(in_bin)
        if bin_count > 0:
            bin_acc = np.mean(y_true[in_bin])
            bin_conf = np.mean(y_prob[in_bin])
            ece += (bin_count / n) * np.abs(bin_acc - bin_conf)

    return float(ece)


def compute_classification_metrics(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    target_precision_threshold: float = 0.50,
) -> Dict[str, Any]:
    """
    Compute comprehensive metrics for binary classification with class-imbalance awareness.
    Records denominators and positive base rates (Principle V / FR-028).
    """
    y_t = np.asarray(y_true, dtype=int)
    y_p = np.clip(np.asarray(y_prob, dtype=float), 1e-7, 1 - 1e-7)

    total_samples = len(y_t)
    positive_count = int(np.sum(y_t))
    positive_rate = float(np.mean(y_t)) if total_samples > 0 else 0.0

    metrics: Dict[str, Any] = {
        "total_samples": total_samples,
        "positive_count": positive_count,
        "positive_base_rate": positive_rate,
    }

    if positive_count == 0 or positive_count == total_samples:
        # Edge case: single class in split
        metrics["pr_auc"] = 0.0
        metrics["roc_auc"] = 0.5
        metrics["brier_score"] = float(brier_score_loss(y_t, y_p)) if total_samples > 0 else 0.0
        metrics["ece"] = 0.0
        metrics["recall_at_precision"] = 0.0
        return metrics

    # PR-AUC & ROC-AUC
    metrics["pr_auc"] = float(average_precision_score(y_t, y_p))
    metrics["roc_auc"] = float(roc_auc_score(y_t, y_p))
    metrics["brier_score"] = float(brier_score_loss(y_t, y_p))
    metrics["log_loss"] = float(log_loss(y_t, y_p))
    metrics["ece"] = compute_expected_calibration_error(y_t, y_p)

    # Recall at fixed precision
    precisions, recalls, thresholds = precision_recall_curve(y_t, y_p)
    valid_recalls = [r for p, r in zip(precisions, recalls) if p >= target_precision_threshold]
    metrics["recall_at_target_precision"] = float(max(valid_recalls)) if valid_recalls else 0.0
    metrics["target_precision_threshold"] = target_precision_threshold

    return metrics
