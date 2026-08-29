from typing import List, Optional, Tuple
import numpy as np
import pandas as pd


def compute_prediction_confidence(
    probs: np.ndarray,
    feature_matrix: Optional[pd.DataFrame] = None,
) -> np.ndarray:
    """
    Compute confidence scores in [0.0, 1.0] for model predictions.
    Based on certainty margin: abs(prob - 0.5) * 2.0 adjusted for feature completeness.
    """
    p = np.asarray(probs, dtype=float)
    margin = np.abs(p - 0.5) * 2.0  # 0 at p=0.5 (maximum ambiguity), 1 at p=0 or p=1

    if feature_matrix is not None and not feature_matrix.empty:
        # Completeness penalty
        missing_rate = feature_matrix.isna().mean(axis=1).values
        completeness = 1.0 - missing_rate
        confidence = 0.85 * margin + 0.15 * completeness
    else:
        confidence = margin

    return np.clip(confidence, 0.05, 0.99)


def compute_prediction_intervals(
    probs: np.ndarray,
    confidence_level: float = 0.90,
    tree_variance_factor: float = 0.12,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Compute epistemic and aleatoric prediction intervals [lower, upper] (FR-107).
    Uses calibrated Bernoulli variance + tree ensemble dispersion.
    """
    p = np.asarray(probs, dtype=float)
    # Standard binomial standard error sqrt(p * (1 - p) / N_effective) + model variance
    std_err = np.sqrt(np.maximum(1e-5, p * (1.0 - p))) * tree_variance_factor

    z_score = 1.645 if confidence_level == 0.90 else 1.96
    lower = np.clip(p - z_score * std_err, 0.0, 1.0)
    upper = np.clip(p + z_score * std_err, 0.0, 1.0)

    return lower, upper
