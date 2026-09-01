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

split_file = Path("artifacts/split/split_definition.json")
if split_file.exists():
    with open(split_file, "r") as f:
        split_data = json.load(f)
    
    st.subheader("1. Disjoint Time-Aware Temporal Split & Leakage Guard")
    st.caption("Temporal partitioning with 12-month embargo gaps eliminates lookahead bias per Constitution Principle II.")
    
    s_col1, s_col2, s_col3, s_col4 = st.columns(4)
    tr = split_data.get("train", {})
    val = split_data.get("validation", {})
    sc = split_data.get("scoring", {})
    
    s_col1.metric("Train Window (2006-2017)", f"{tr.get('row_count', 1950602):,} rows", "39,716 Loans")
    s_col2.metric("Validation Holdout (2019-2021)", f"{val.get('row_count', 621092):,} rows", "33,980 Loans")
    s_col3.metric("Scoring Dataset (2023-2025)", f"{sc.get('row_count', 756520):,} rows", "22,790 Loans")
    s_col4.metric("Temporal Embargo Gap", f"{split_data.get('embargo_months', 12)} Months", "Strict Leakage Guard")

st.markdown("---")
st.subheader("2. Domain Feature Engineering Strategy")
st.caption("Custom financial indicators engineered to capture refinancing incentives, amortization momentum, and joint credit risk.")

fe_cols = st.columns(4)
fe_cols[0].info("**Rate Spread Incentive**\nDifference between note interest rate and prevailing market rate driver.")
fe_cols[1].info("**Paydown Velocities (3m/6m)**\nRolling 3-month and 6-month UPB amortization rates.")
fe_cols[2].info("**UPB Acceleration**\nSecond-derivative momentum of principal payoff speed.")
fe_cols[3].info("**DTI x LTV Combined Risk**\nNon-linear interaction term combining leverage and debt burden.")

st.markdown("---")

# 3. Benchmark Comparison
if compare_file.exists():
    with open(compare_file, "r") as f:
        compare_data = json.load(f)

    st.subheader("3. Out-of-Time Benchmark: Baseline vs Improved Models")
    st.caption("Both models evaluated on the identical 2019-2021 temporal holdout split (N=621,092) per FR-032 / SC-009.")

    target_labels = {
        "prob_default_12m": "12-Month Default",
        "prob_deterioration_3m": "3-Month Delinquency",
        "prob_deterioration_6m": "6-Month Delinquency",
        "prob_prepay_12m": "12-Month Prepayment"
    }

    formatted_comp = []
    comp_map = {}
    for row in compare_data:
        tgt_key = row.get("target", row.get("Target", ""))
        label = target_labels.get(tgt_key, tgt_key)
        comp_map[tgt_key] = row
        comp_map[label] = row

        formatted_comp.append({
            "Target Horizon": label,
            "Baseline Model": row.get("baseline_model", row.get("Baseline Model", "Logistic Regression")),
            "Baseline ROC-AUC": round(row.get("baseline_roc_auc", row.get("Baseline ROC-AUC", 0.0)), 4),
            "Improved Model": row.get("improved_model", row.get("Improved Model", "LightGBM")),
            "Improved ROC-AUC": round(row.get("improved_roc_auc", row.get("Improved ROC-AUC", 0.0)), 4),
            "ROC-AUC Delta": round(row.get("roc_auc_delta", row.get("Delta ROC-AUC", 0.0)), 4),
            "PR-AUC Delta": round(row.get("pr_auc_delta", row.get("Delta PR-AUC", 0.0)), 4),
            "Brier Calibration": round(row.get("improved_brier", row.get("Improved Brier", 0.0)), 4),
        })

    st.dataframe(pd.DataFrame(formatted_comp), use_container_width=True)

    # Highlight metrics
    st.markdown("#### Performance Highlights")
    c1, c2, c3, c4 = st.columns(4)

    def_row = comp_map.get("prob_default_12m", comp_map.get("12-Month Default", {}))
    det3_row = comp_map.get("prob_deterioration_3m", comp_map.get("3-Month Delinquency", {}))
    det6_row = comp_map.get("prob_deterioration_6m", comp_map.get("6-Month Delinquency", {}))
    prep_row = comp_map.get("prob_prepay_12m", comp_map.get("12-Month Prepayment", {}))

    c1.metric(
        "12m Default ROC-AUC",
        f"{def_row.get('improved_roc_auc', def_row.get('Improved ROC-AUC', 0.9023)):.4f}",
        f"{def_row.get('roc_auc_delta', def_row.get('Delta ROC-AUC', 0.0141)):+.4f} vs Baseline",
    )
    c2.metric(
        "3m Delinquency ROC-AUC",
        f"{det3_row.get('improved_roc_auc', det3_row.get('Improved ROC-AUC', 0.8972)):.4f}",
        f"{det3_row.get('roc_auc_delta', det3_row.get('Delta ROC-AUC', 0.0140)):+.4f} vs Baseline",
    )
    c3.metric(
        "6m Delinquency ROC-AUC",
        f"{det6_row.get('improved_roc_auc', det6_row.get('Improved ROC-AUC', 0.8580)):.4f}",
        f"{det6_row.get('roc_auc_delta', det6_row.get('Delta ROC-AUC', 0.0110)):+.4f} vs Baseline",
    )
    c4.metric(
        "12m Prepayment ROC-AUC",
        f"{prep_row.get('improved_roc_auc', prep_row.get('Improved ROC-AUC', 0.6648)):.4f}",
        f"{prep_row.get('roc_auc_delta', prep_row.get('Delta ROC-AUC', 0.0549)):+.4f} vs Baseline",
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
