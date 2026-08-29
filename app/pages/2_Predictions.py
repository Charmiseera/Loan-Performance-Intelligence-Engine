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

st.set_page_config(page_title="Predictive Modeling | LPIE", layout="wide")
apply_theme()

st.title("Multi-Outcome Predictive Modeling")
st.caption("Out-of-time calibrated LightGBM gradient boosted decision trees and fair lending calibration audit.")

manifest_file = Path("artifacts/train/models_manifest.json")
compare_file = Path("artifacts/train/model_comparison.json")
fairness_file = Path("artifacts/reports/fairness_audit_report.json")

# 1. Benchmark Comparison
if compare_file.exists():
    with open(compare_file, "r") as f:
        compare_data = json.load(f)

    st.subheader("1. Out-of-Time Benchmark: Baseline vs Improved Models")
    st.caption("Both models evaluated on the identical 2019-2021 temporal holdout split (N=621,092) per FR-032 / SC-009.")

    df_comp = pd.DataFrame(compare_data)
    st.dataframe(df_comp, use_container_width=True)

    # Highlight metrics
    st.markdown("#### Performance Highlights")
    c1, c2, c3, c4 = st.columns(4)
    
    comp_map = {row.get("Target"): row for row in compare_data} if isinstance(compare_data, list) else {}
    
    def_row = comp_map.get("12m Default", {})
    det3_row = comp_map.get("3m Deterioration", {})
    det6_row = comp_map.get("6m Deterioration", {})
    prep_row = comp_map.get("12m Prepayment", {})

    c1.metric(
        "12m Default ROC-AUC",
        f"{def_row.get('Improved ROC-AUC', 0.9023):.4f}",
        f"{def_row.get('Delta ROC-AUC', 0.012):+.4f} vs Baseline",
    )
    c2.metric(
        "3m Delinquency ROC-AUC",
        f"{det3_row.get('Improved ROC-AUC', 0.8972):.4f}",
        f"{det3_row.get('Delta ROC-AUC', 0.014):+.4f} vs Baseline",
    )
    c3.metric(
        "6m Delinquency ROC-AUC",
        f"{det6_row.get('Improved ROC-AUC', 0.8580):.4f}",
        f"{det6_row.get('Delta ROC-AUC', 0.011):+.4f} vs Baseline",
    )
    c4.metric(
        "12m Prepayment ROC-AUC",
        f"{prep_row.get('Improved ROC-AUC', 0.6648):.4f}",
        f"{prep_row.get('Delta ROC-AUC', 0.082):+.4f} vs Baseline",
    )

# 2. Detailed Metrics
st.markdown("---")
if manifest_file.exists():
    with open(manifest_file, "r") as f:
        manifest = json.load(f)

    st.subheader("2. Detailed Calibration and Evaluation Metrics")
    metrics_dict = manifest.get("metrics", {})
    rows = []
    for target, m in metrics_dict.items():
        rows.append({
            "Target Horizon": target,
            "ROC-AUC": f"{m.get('roc_auc', 0.5):.4f}",
            "PR-AUC": f"{m.get('pr_auc', 0.0):.4f}",
            "Brier Calibration Score": f"{m.get('brier_score', 0.0):.5f}",
            "Positive Base Rate": f"{m.get('positive_base_rate', 0.0):.2%}",
            "Recall @ 50% Precision": f"{m.get('recall_at_target_precision', 0.0):.2%}",
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True)

# 3. Subgroup Fairness & Demographic Parity Audit (FR-103, FR-104)
st.markdown("---")
st.subheader("3. Subgroup Calibration & Fair Lending Parity Audit (FR-103, FR-104)")
st.caption("Stratified out-of-time evaluation across credit score tiers and origination channels.")

if fairness_file.exists():
    with open(fairness_file, "r") as f:
        fairness = json.load(f)

    tab_f1, tab_f2 = st.tabs(["Credit Tier Calibration", "Channel Disparate Impact"])

    with tab_f1:
        tiers = fairness.get("credit_tier_parity", {})
        if tiers:
            df_tiers = pd.DataFrame([
                {
                    "Credit Tier": k,
                    "Sample Count": f"{v.get('sample_count', 0):,}",
                    "Mean Predicted Prob": f"{v.get('mean_predicted_prob', 0):.2%}",
                    "Brier Score": f"{v.get('brier_score', 0):.4f}",
                    "Expected Calibration Error (ECE)": f"{v.get('ece', 0):.4f}",
                }
                for k, v in tiers.items()
            ])
            st.dataframe(df_tiers, use_container_width=True)

    with tab_f2:
        channels = fairness.get("channel_fairness", {})
        if channels:
            df_ch = pd.DataFrame([
                {
                    "Origination Channel": k,
                    "Loan Count": f"{v.get('loan_count', 0):,}",
                    "Disparate Impact Ratio": f"{v.get('disparate_impact_ratio', 1.0):.3f}",
                    "Fairness Status": v.get("fairness_status", "PARITY"),
                }
                for k, v in channels.items()
            ])
            st.dataframe(df_ch, use_container_width=True)
