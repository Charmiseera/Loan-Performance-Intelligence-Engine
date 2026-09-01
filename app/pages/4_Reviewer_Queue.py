import sys
from pathlib import Path

# Ensure src/ is on sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import streamlit as st
import json
import pandas as pd
from lpie.ui.theme import apply_theme

st.set_page_config(page_title="Anomaly Reviewer Queue | LPIE", layout="wide")
apply_theme()

st.title("Anomaly Intelligence & Prioritized Reviewer Queue")
st.caption("Hybrid deterministic rule violations combined with IsolationForest anomaly scoring weighted by UPB exposure.")

queue_file = Path("artifacts/anomaly/reviewer_queue.json")
reconcil_file = Path("artifacts/anomaly/reconciliation_fixture.parquet")

if queue_file.exists():
    with open(queue_file, "r") as f:
        queue_data = json.load(f)

    st.subheader("1. Prioritized Operational Triage Queue (Top Exceptions)")
    st.caption("Ordered strictly by composite priority score: Rule Severity (40%), Unsupervised Isolation Score (30%), and UPB Exposure (30%).")

    loans_list = queue_data.get("loans", queue_data) if isinstance(queue_data, dict) else queue_data
    formatted_queue = []
    for item in loans_list:
        formatted_queue.append({
            "Queue Rank": item.get("queue_rank", "N/A"),
            "Loan ID": item.get("loan_id", "N/A"),
            "Priority Score": round(item.get("priority_score", 0.0), 4),
            "Anomaly Score": round(item.get("anomaly_score", 0.0), 4),
            "Flag Source": item.get("flag_source", "").replace("_", " "),
            "Exception Type": item.get("exception_type", "").replace("_", " "),
            "Recommended Action": item.get("recommended_action", "").replace("_", " "),
            "Reporting Month": item.get("reporting_month", "N/A"),
        })

    df_queue = pd.DataFrame(formatted_queue)
    st.dataframe(df_queue, use_container_width=True)

if reconcil_file.exists():
    st.markdown("---")
    st.subheader("2. Servicer Reconciliation Conflict Audit")
    st.caption("Simulated multi-servicer reporting discrepancy fixture evaluating payment vs balance variance (FR-043, SC-026).")
    df_rec = pd.read_parquet(reconcil_file).head(20)
    st.dataframe(df_rec, use_container_width=True)
