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

st.set_page_config(page_title="Macro Scenario Simulation | LPIE", layout="wide")
apply_theme()

st.title("Macroeconomic Scenario & Monte Carlo Portfolio Stress Simulation")
st.caption("Stochastic loss distributions, Value-at-Risk (VaR), and macroeconomic shock transition analysis.")

proj_file = Path("artifacts/scenario/scenario_projections.json")
breakdown_file = Path("artifacts/scenario/scenario_segment_breakdown.json")
mc_file = Path("artifacts/scenario/monte_carlo_results.json")

if proj_file.exists():
    with open(proj_file, "r") as f:
        projections = json.load(f)

    st.subheader("1. Portfolio-Level Stress Projections")
    st.caption("All scenario parameters represent stated macroeconomic assumptions (FR-051), not economic forecasts.")

    base_def = projections["baseline"]["projected_default_rate"]
    base_prep = projections["baseline"]["projected_prepay_rate"]
    base_det = projections["baseline"]["projected_deterioration_rate"]

    adv_def = projections["adverse"]["projected_default_rate"]
    adv_prep = projections["adverse"]["projected_prepay_rate"]
    adv_det = projections["adverse"]["projected_deterioration_rate"]

    high_def = projections["high_prepayment"]["projected_default_rate"]
    high_prep = projections["high_prepayment"]["projected_prepay_rate"]
    high_det = projections["high_prepayment"]["projected_deterioration_rate"]

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("#### Baseline Scenario")
        st.metric("12m Default Rate", f"{base_def:.2%}")
        st.metric("12m Prepayment Rate", f"{base_prep:.2%}")
        st.metric("6m Deterioration Rate", f"{base_det:.2%}")

    with c2:
        st.markdown("#### Adverse Credit Stress")
        st.metric("12m Default Rate", f"{adv_def:.2%}", delta=f"{adv_def - base_def:+.2%} vs Baseline", delta_color="inverse")
        st.metric("12m Prepayment Rate", f"{adv_prep:.2%}", delta=f"{adv_prep - base_prep:+.2%} vs Baseline")
        st.metric("6m Deterioration Rate", f"{adv_det:.2%}", delta=f"{adv_det - base_det:+.2%} vs Baseline", delta_color="inverse")

    with c3:
        st.markdown("#### High Prepayment Wave")
        st.metric("12m Default Rate", f"{high_def:.2%}", delta=f"{high_def - base_def:+.2%} vs Baseline")
        st.metric("12m Prepayment Rate", f"{high_prep:.2%}", delta=f"{high_prep - base_prep:+.2%} vs Baseline")
        st.metric("6m Deterioration Rate", f"{high_det:.2%}", delta=f"{high_det - base_det:+.2%} vs Baseline")

# 2. Monte Carlo Portfolio Simulation
st.markdown("---")
st.subheader("2. Monte Carlo Stochastic Loss & Prepayment Simulation (FR-101, FR-102)")
st.caption("10,000-path stochastic loss simulation incorporating loan-level default probabilities and Beta loss severity.")

if mc_file.exists():
    with open(mc_file, "r") as f:
        mc = json.load(f)

    mc1, mc2, mc3, mc4 = st.columns(4)
    mc1.metric("Expected Portfolio Loss", f"${mc.get('expected_loss', 0):,.0f}", f"{mc.get('expected_loss_rate', 0):.2%} Loss Rate")
    mc2.metric("Value-at-Risk (95% VaR)", f"${mc.get('var_95', 0):,.0f}")
    mc3.metric("Value-at-Risk (99% VaR)", f"${mc.get('var_99', 0):,.0f}")
    mc4.metric("99% Expected Shortfall (CVaR)", f"${mc.get('cvar_99', 0):,.0f}")

    pcts = mc.get("loss_percentiles", {})
    if pcts:
        st.markdown("#### Portfolio Loss Distribution Percentiles")
        df_pct = pd.DataFrame([
            {"Percentile": k.upper(), "Simulated Portfolio Loss ($)": v}
            for k, v in pcts.items()
        ])
        st.bar_chart(df_pct.set_index("Percentile"))

# 3. Segment Breakdown
st.markdown("---")
if breakdown_file.exists():
    with open(breakdown_file, "r") as f:
        breakdowns = json.load(f)

    st.subheader("3. Segment-Level Breakdown (Geography / Servicer / Purpose)")
    scenario_sel = st.selectbox("Select Scenario", ["baseline", "adverse", "high_prepayment"])
    seg_data = breakdowns.get(scenario_sel, {})
    if seg_data:
        dim_sel = st.selectbox("Select Segment Dimension", list(seg_data.keys()))
        dim_vals = seg_data.get(dim_sel, {})
        rows = []
        for val, stats in dim_vals.items():
            rows.append({
                dim_sel: val,
                "Loan Count": stats.get("loan_count", 0),
                "Projected Default Rate": f"{stats.get('projected_default_rate', 0):.2%}",
                "Projected Prepayment Rate": f"{stats.get('projected_prepay_rate', 0):.2%}",
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True)

# 4. Scenario Transition Shift
st.markdown("---")
st.subheader("4. 12-Month Macro Stress Transition Shift")
if proj_file.exists():
    trans_df = pd.DataFrame([
        {
            "State": "Current (Performing)",
            "Baseline Probability": f"{1.0 - base_def - base_prep:.2%}",
            "Adverse Credit Stress": f"{1.0 - adv_def - adv_prep:.2%}",
            "High Prepayment Wave": f"{1.0 - high_def - high_prep:.2%}",
        },
        {
            "State": "Delinquent / Deterioration (6m)",
            "Baseline Probability": f"{base_det:.2%}",
            "Adverse Credit Stress": f"{adv_det:.2%}",
            "High Prepayment Wave": f"{high_det:.2%}",
        },
        {
            "State": "Default / REO (12m)",
            "Baseline Probability": f"{base_def:.2%}",
            "Adverse Credit Stress": f"{adv_def:.2%}",
            "High Prepayment Wave": f"{high_def:.2%}",
        },
        {
            "State": "Prepaid (12m)",
            "Baseline Probability": f"{base_prep:.2%}",
            "Adverse Credit Stress": f"{adv_prep:.2%}",
            "High Prepayment Wave": f"{high_prep:.2%}",
        },
    ])
    st.dataframe(trans_df, use_container_width=True)
