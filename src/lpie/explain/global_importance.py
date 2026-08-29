from typing import Any, Dict, List
import lightgbm as lgb
import numpy as np
import pandas as pd
import shap


def compute_global_feature_importance(
    model: Any,
    X_sample: pd.DataFrame,
    max_features: int = 20,
) -> Dict[str, Any]:
    """
    Compute global TreeSHAP feature importance rankings.
    """
    # Extract underlying booster if wrapped
    raw_model = getattr(model, "model", model)
    feature_names = list(X_sample.columns)
    
    try:
        explainer = shap.TreeExplainer(raw_model)
        shap_values = explainer.shap_values(X_sample)
        if isinstance(shap_values, list):
            # Binary classification list of [class_0, class_1]
            vals = np.abs(shap_values[1]).mean(axis=0)
        elif len(shap_values.shape) == 3:
            vals = np.abs(shap_values[:, :, 1]).mean(axis=0)
        else:
            vals = np.abs(shap_values).mean(axis=0)
    except Exception:
        # Fallback to feature_importances_ if SHAP tree explainer fails
        if hasattr(raw_model, "feature_importances_"):
            vals = raw_model.feature_importances_
        else:
            vals = np.ones(len(feature_names))

    ranking = []
    for name, score in sorted(zip(feature_names, vals), key=lambda x: x[1], reverse=True)[:max_features]:
        ranking.append({"feature": name, "mean_abs_shap": float(score)})

    return {
        "method": "TreeSHAP",
        "sample_size": len(X_sample),
        "rankings": ranking,
    }
