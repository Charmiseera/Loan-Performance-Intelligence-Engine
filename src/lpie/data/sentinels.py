from typing import Any, Dict, List, Tuple
import numpy as np
import pandas as pd


def apply_sentinel_policy(
    df: pd.DataFrame,
    sentinel_map: Dict[str, List[Any]],
) -> Tuple[pd.DataFrame, Dict[str, Dict[str, Any]]]:
    """
    Replace documented per-field sentinel values with np.nan.
    Does not use a global sentinel list, preventing label corruption (e.g. DelinquencyStatus=99 is valid).
    Returns cleaned DataFrame and an audit dictionary recording replacement counts per field.
    """
    df_clean = df.copy()
    audit: Dict[str, Dict[str, Any]] = {}

    for col, sentinels in sentinel_map.items():
        if col not in df_clean.columns:
            continue
        
        replaced_count = 0
        for val in sentinels:
            mask = df_clean[col] == val
            cnt = int(mask.sum())
            if cnt > 0:
                df_clean.loc[mask, col] = np.nan
                replaced_count += cnt
                
        audit[col] = {
            "sentinels": sentinels,
            "replaced_count": replaced_count,
            "null_pct_after": float(df_clean[col].isna().mean() * 100),
        }

    return df_clean, audit


def extract_sentinel_audit(audit: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """Summarize sentinel replacement statistics for reporting."""
    total_replaced = sum(item["replaced_count"] for item in audit.values())
    affected_fields = [k for k, item in audit.items() if item["replaced_count"] > 0]
    return {
        "total_sentinel_values_reinterpreted": total_replaced,
        "affected_field_count": len(affected_fields),
        "affected_fields": affected_fields,
        "details": audit,
    }
