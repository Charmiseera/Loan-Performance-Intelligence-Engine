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
from lpie.explain.counterfactual import generate_sparse_counterfactual

st.set_page_config(page_title="Model Explainability | LPIE", layout="wide")
apply_theme()

st.title("Model Explainability, Attribution & Counterfactuals")
st.caption("TreeSHAP attribution, actionable sparse counterfactual search, and classification error casebook.")

glob_file = Path("artifacts/explain/global_importance.json")
error_file = Path("artifacts/explain/error_casebook.json")

# 1. Global Feature Importance
if glob_file.exists():
    with open(glob_file, "r") as f:
        glob_data = json.load(f)

    st.subheader("1. Global Feature Importance (TreeSHAP)")
    st.caption("Mean absolute SHAP value rankings across portfolio training population.")
    rankings = glob_data.get("rankings", [])
    if rankings:
        df_rank = pd.DataFrame(rankings).head(10)
        st.dataframe(df_rank, use_container_width=True)

# 2. Counterfactual "What-If" Risk Mitigations (FR-105)
st.markdown("---")
st.subheader("2. Sparse Counterfactual \"What-If\" Risk Mitigations (FR-105)")
st.caption("Actionable perturbations optimizing feature values to lower loan default risk while strictly preserving immutable characteristics.")

col_cf1, col_cf2, col_cf3 = st.columns(3)
with col_cf1:
    test_upb = st.number_input("Current UPB ($)", value=280000.0, step=10000.0)
    test_dti = st.slider("Debt-to-Income Ratio (%)", 15.0, 60.0, 44.0)
with col_cf2:
    test_rate = st.slider("Current Interest Rate (%)", 3.0, 9.0, 6.75)
    test_score = st.number_input("Credit Score (Immutable)", value=645.0, disabled=True)
with col_cf3:
    base_risk = st.slider("Predicted 12m Default Probability", 0.05, 0.40, 0.185)
    target_risk = st.slider("Target Default Probability", 0.01, 0.08, 0.030)

cf_result = generate_sparse_counterfactual(
    loan_profile={
        "loan_id": "DEMO_LOAN_CF",
        "current_actual_upb": test_upb,
        "original_dti": test_dti,
        "rate_spread_incentive": test_rate - 5.5,
        "credit_score": test_score,
    },
    baseline_prob=base_risk,
    target_prob=target_risk,
)

st.markdown("#### Recommended Actionable Mitigations")
perturbations = cf_result.get("actionable_perturbations", {})
if perturbations:
    for feat, detail in perturbations.items():
        st.info(f"Action: {detail.get('action')} (Current: {detail.get('current')} -> Recommended: {detail.get('recommended')})")
else:
    st.success("Baseline probability already satisfies the target risk threshold.")

# 3. Error Analysis
st.markdown("---")
if error_file.exists():
    with open(error_file, "r") as f:
        err_data = json.load(f)

    st.subheader("3. Error Analysis & Casebook (FP / FN Studies)")
    c1, c2 = st.columns(2)
    c1.metric("False Positives Identified", f"{err_data.get('false_positive_count', 0):,}")
    c2.metric("False Negatives Identified", f"{err_data.get('false_negative_count', 0):,}")

    st.markdown("#### False Positive Case Studies (High Predicted Risk, Zero Realized Event)")
    fp_cases = err_data.get("false_positive_cases", [])
    if fp_cases:
        st.json(fp_cases)

    st.markdown("#### False Negative Case Studies (Low Predicted Risk, Realized Default)")
    fn_cases = err_data.get("false_negative_cases", [])
    if fn_cases:
        st.json(fn_cases)
