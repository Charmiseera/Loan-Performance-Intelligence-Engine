from typing import Tuple
import numpy as np
import pandas as pd


def compute_composite_anomaly_score(
    statistical_scores: np.ndarray,
    rule_violation_counts: pd.Series,
) -> Tuple[np.ndarray, np.ndarray, pd.Series]:
    """
    Combine deterministic rule violations and statistical anomaly scores.
    Returns:
    - composite_anomaly_score: np.ndarray in [0, 1]
    - exception_required: boolean np.ndarray
    - exception_type: pd.Series of taxonomy strings
    """
    stat_s = np.asarray(statistical_scores, dtype=float)
    rule_counts = rule_violation_counts.values
    
    # Composite formula: 60% statistical anomaly + 40% rule severity
    rule_component = np.clip(rule_counts * 0.35, 0.0, 1.0)
    composite = 0.6 * stat_s + 0.4 * rule_component
    composite = np.clip(composite, 0.0, 1.0)

    # Exception required if severe rule violation OR composite score >= 0.70
    exception_req = (rule_counts >= 1) | (composite >= 0.70)

    # Determine exception type
    types = []
    for r_cnt, s_score in zip(rule_counts, composite):
        if r_cnt >= 2:
            types.append("MULTI_RULE_VIOLATION")
        elif r_cnt == 1:
            types.append("INTEGRITY_EXCEPTION")
        elif s_score >= 0.85:
            types.append("EXTREME_STATISTICAL_OUTLIER")
        elif s_score >= 0.70:
            types.append("DELINQUENCY_ACCELERATION")
        else:
            types.append("NONE")

    return composite, exception_req, pd.Series(types, index=rule_violation_counts.index)
