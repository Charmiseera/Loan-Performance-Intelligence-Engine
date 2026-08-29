from typing import Any, Dict, List
import pandas as pd
import numpy as np


def analyze_model_errors(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    feature_matrix: pd.DataFrame,
    threshold: float = 0.5,
    top_k_cases: int = 5,
) -> Dict[str, Any]:
    """
    Identifies and analyzes concrete false-positive and false-negative cases
    with their driving attributes (FR-055, SC-019).

    - False Positive (FP): Predicted positive (prob >= threshold) but actual was 0.
    - False Negative (FN): Predicted negative (prob < threshold) but actual was 1.
    """
    y_true = np.array(y_true)
    y_prob = np.array(y_prob)

    y_pred = (y_prob >= threshold).astype(int)

    fp_indices = np.where((y_pred == 1) & (y_true == 0))[0]
    fn_indices = np.where((y_pred == 0) & (y_true == 1))[0]

    # Sort FPs by highest predicted probability (most confident errors)
    if len(fp_indices) > 0:
        fp_sorted = fp_indices[np.argsort(-y_prob[fp_indices])][:top_k_cases]
    else:
        fp_sorted = []

    # Sort FNs by lowest predicted probability (most missed errors)
    if len(fn_indices) > 0:
        fn_sorted = fn_indices[np.argsort(y_prob[fn_indices])][:top_k_cases]
    else:
        fn_sorted = []

    def _extract_case_info(indices, error_type):
        cases = []
        for idx in indices:
            row_feats = feature_matrix.iloc[idx].to_dict() if idx < len(feature_matrix) else {}
            # Pick prominent numerical features
            num_feats = {k: v for k, v in row_feats.items() if isinstance(v, (int, float)) and not np.isnan(v)}
            cases.append({
                "index": int(idx),
                "error_type": error_type,
                "predicted_probability": round(float(y_prob[idx]), 4),
                "actual_outcome": int(y_true[idx]),
                "key_feature_values": {k: round(float(v), 2) for k, v in list(num_feats.items())[:6]},
            })
        return cases

    fp_cases = _extract_case_info(fp_sorted, "FALSE_POSITIVE")
    fn_cases = _extract_case_info(fn_sorted, "FALSE_NEGATIVE")

    return {
        "decision_threshold": threshold,
        "total_evaluated": len(y_true),
        "false_positive_count": len(fp_indices),
        "false_negative_count": len(fn_indices),
        "false_positive_cases": fp_cases,
        "false_negative_cases": fn_cases,
        "error_narrative": (
            f"Evaluated {len(y_true):,} cases. Identified {len(fp_indices):,} False Positives "
            f"and {len(fn_indices):,} False Negatives at threshold {threshold:.2f}."
        ),
    }
