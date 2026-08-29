from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd


def compute_column_statistics(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Computes per-column summary stats: dtypes, missingness counts & rates,
    distinct counts, percentiles for numeric columns, top categories for non-numeric (FR-010).
    """
    total_rows = len(df)
    stats: Dict[str, Any] = {}

    for col in df.columns:
        s = df[col]
        null_count = int(s.isna().sum())
        null_rate = float(null_count / total_rows) if total_rows > 0 else 0.0
        n_unique = int(s.nunique(dropna=True))

        col_stat: Dict[str, Any] = {
            "dtype": str(s.dtype),
            "total_count": total_rows,
            "null_count": null_count,
            "null_rate": round(null_rate, 5),
            "distinct_count": n_unique,
        }

        if pd.api.types.is_numeric_dtype(s):
            valid_vals = s.dropna()
            if not valid_vals.empty:
                col_stat.update({
                    "min": float(valid_vals.min()),
                    "max": float(valid_vals.max()),
                    "mean": round(float(valid_vals.mean()), 4),
                    "std": round(float(valid_vals.std()), 4) if len(valid_vals) > 1 else 0.0,
                    "p25": round(float(valid_vals.quantile(0.25)), 4),
                    "p50": round(float(valid_vals.median()), 4),
                    "p75": round(float(valid_vals.quantile(0.75)), 4),
                })
        else:
            top_vals = s.value_counts(dropna=True).head(5).to_dict()
            col_stat["top_values"] = {str(k): int(v) for k, v in top_vals.items()}

        stats[col] = col_stat

    return stats


def detect_missingness_patterns(df: pd.DataFrame, top_k: int = 10) -> List[Dict[str, Any]]:
    """
    Identifies co-occurring missingness combinations across columns (FR-011).
    """
    if df.empty:
        return []

    null_mask = df.isna()
    # Find columns that have at least one null
    cols_with_nulls = [c for c in df.columns if null_mask[c].any()]
    if not cols_with_nulls:
        return []

    pattern_df = null_mask[cols_with_nulls].astype(int)
    pattern_counts = pattern_df.groupby(cols_with_nulls).size().reset_index(name="count")
    pattern_counts = pattern_counts.sort_values(by="count", ascending=False).head(top_k)

    patterns = []
    for _, row in pattern_counts.iterrows():
        missing_cols = [c for c in cols_with_nulls if row[c] == 1]
        patterns.append({
            "missing_fields": missing_cols,
            "missing_field_count": len(missing_cols),
            "record_count": int(row["count"]),
            "share_of_total": round(float(row["count"] / len(df)), 5),
        })

    return patterns
