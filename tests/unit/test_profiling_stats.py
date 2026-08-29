import pandas as pd
import numpy as np
from lpie.data.profile_stats import compute_column_statistics, detect_missingness_patterns


def test_compute_column_statistics():
    df = pd.DataFrame({
        "credit_score": [700, 720, 750, np.nan],
        "state": ["CA", "NY", "CA", "TX"],
        "is_active": [1, 0, 1, 1],
    })

    stats = compute_column_statistics(df)
    assert "credit_score" in stats
    assert stats["credit_score"]["null_count"] == 1
    assert stats["credit_score"]["null_rate"] == 0.25
    assert stats["credit_score"]["min"] == 700.0
    assert stats["credit_score"]["max"] == 750.0

    assert "state" in stats
    assert stats["state"]["distinct_count"] == 3
    assert stats["state"]["top_values"]["CA"] == 2


def test_detect_missingness_patterns():
    df = pd.DataFrame({
        "a": [1, np.nan, np.nan, 4],
        "b": [1, np.nan, np.nan, 4],
        "c": [1, 2, np.nan, 4],
    })

    patterns = detect_missingness_patterns(df)
    assert len(patterns) > 0
    # Both a and b are missing together in row index 1 and 2
    top_pat = patterns[0]
    assert "record_count" in top_pat
    assert top_pat["record_count"] >= 1
