import numpy as np
import pandas as pd
from lpie.explain.error_analysis import analyze_model_errors


def test_analyze_model_errors():
    y_true = np.array([0, 0, 1, 1, 0])
    y_prob = np.array([0.9, 0.1, 0.1, 0.8, 0.2]) # index 0 is FP, index 2 is FN
    df_feats = pd.DataFrame({
        "credit_score": [650, 750, 600, 580, 720],
        "dti": [45, 20, 50, 55, 25],
    })

    res = analyze_model_errors(y_true, y_prob, df_feats, threshold=0.5)
    assert res["false_positive_count"] == 1
    assert res["false_negative_count"] == 1
    assert len(res["false_positive_cases"]) == 1
    assert res["false_positive_cases"][0]["predicted_probability"] == 0.9
    assert len(res["false_negative_cases"]) == 1
    assert res["false_negative_cases"][0]["predicted_probability"] == 0.1
