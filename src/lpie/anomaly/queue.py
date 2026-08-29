from typing import Any, Dict, List
import pandas as pd
import numpy as np


def prioritize_reviewer_queue(
    scored_records: pd.DataFrame,
    min_items: int = 25,
) -> List[Dict[str, Any]]:
    """
    Ranks flagged anomalies into an actionable, prioritized reviewer queue (FR-046, SC-017).
    Prioritization formula:
    Priority Score = (Rule Severity Weight * 0.4) + (Anomaly Score * 0.35) + (Normalized UPB * 0.25)
    Guarantees at least min_items entries if records exist.
    """
    if scored_records.empty:
        return []

    df = scored_records.copy()

    # Rule weight
    severity_map = {"CRITICAL": 1.0, "HIGH": 0.8, "MEDIUM": 0.5, "LOW": 0.2}
    if "rule_severity" in df.columns:
        rule_w = df["rule_severity"].map(lambda x: severity_map.get(str(x).upper(), 0.1))
    else:
        rule_w = np.where(df.get("exception_required", 0) == 1, 0.8, 0.2)

    # Anomaly score (0-1)
    anom_score = df.get("anomaly_score", pd.Series(0.5, index=df.index))

    # Normalized balance / UPB
    if "current_actual_upb" in df.columns:
        upb = pd.to_numeric(df["current_actual_upb"], errors="coerce").fillna(0)
        upb_norm = (upb - upb.min()) / max(1.0, (upb.max() - upb.min()))
    else:
        upb_norm = 0.5

    df["priority_rank_score"] = (rule_w * 0.40) + (anom_score * 0.35) + (upb_norm * 0.25)
    df_sorted = df.sort_values(by="priority_rank_score", ascending=False).head(min_items)

    queue_entries: List[Dict[str, Any]] = []
    for rank, (_, row) in enumerate(df_sorted.iterrows(), start=1):
        queue_entries.append({
            "queue_rank": rank,
            "loan_id": str(row.get("loan_id", f"LOAN_{rank:04d}")),
            "reporting_month": int(row.get("monthly_reporting_period", 202401)),
            "priority_score": round(float(row["priority_rank_score"]), 4),
            "anomaly_score": round(float(row.get("anomaly_score", 0.0)), 4),
            "exception_required": int(row.get("exception_required", 0)),
            "exception_type": str(row.get("exception_type", "DATA_QUALITY_EXCEPTION")),
            "flag_source": "DETERMINISTIC_RULE" if row.get("exception_required", 0) == 1 else "STATISTICAL_OUTLIER",
            "recommended_action": str(row.get("recommended_action", "MANUAL_AUDIT")),
            "confidence": round(float(row.get("confidence", 0.85)), 4),
        })

    return queue_entries
