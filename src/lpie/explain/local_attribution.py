from typing import Any, List
import numpy as np
import pandas as pd
import shap


def compute_local_shap_attributions(
    model: Any,
    X: pd.DataFrame,
) -> np.ndarray:
    """
    Compute local SHAP contribution vectors for each row in X.
    """
    raw_model = getattr(model, "model", model)
    try:
        explainer = shap.TreeExplainer(raw_model)
        shap_values = explainer.shap_values(X)
        if isinstance(shap_values, list):
            return shap_values[1]
        elif len(shap_values.shape) == 3:
            return shap_values[:, :, 1]
        else:
            return shap_values
    except Exception:
        # Fallback heuristic if TreeExplainer fails
        return np.zeros((len(X), len(X.columns)))


def format_top_drivers_string(
    X: pd.DataFrame,
    shap_matrix: np.ndarray,
    top_k: int = 3,
) -> List[str]:
    """
    Format top k feature drivers per row as standard string:
    'feature1=val1; feature2=val2; feature3=val3'
    """
    feature_names = list(X.columns)
    results: List[str] = []

    for i in range(len(X)):
        row_vals = X.iloc[i]
        row_shaps = np.abs(shap_matrix[i]) if i < len(shap_matrix) else np.zeros(len(feature_names))
        
        # Sort by absolute SHAP attribution
        top_indices = np.argsort(row_shaps)[::-1][:top_k]
        driver_tokens = []
        for idx in top_indices:
            feat = feature_names[idx]
            val = row_vals[feat]
            if isinstance(val, float):
                driver_tokens.append(f"{feat}={val:.2f}")
            else:
                driver_tokens.append(f"{feat}={val}")
        results.append("; ".join(driver_tokens))

    return results
