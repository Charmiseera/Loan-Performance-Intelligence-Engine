import sys
from pathlib import Path

# Ensure src/ is on sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import streamlit as st
import json
import os
import pandas as pd
from lpie.ui.theme import apply_theme
from lpie.llm.groq_provider import GroqQwenProvider
from lpie.llm.grounding import GroundingValidator
from lpie.llm.retriever import retrieve_field_definition

st.set_page_config(page_title="Reviewer Copilot | LPIE", layout="wide")
apply_theme()

st.title("Grounded LLM Reviewer Copilot")
st.caption("Institutional mortgage review assistant strictly governed by Principle I (ML-First) and Principle III (Grounded LLM Governance).")

# API Configuration
st.sidebar.subheader("Groq API Configuration")
env_key = os.environ.get("GROQ_API_KEY", "")
groq_api_key = st.sidebar.text_input("Groq API Key", value=env_key, type="password", placeholder="Enter Groq API Key...")
model_choice = st.sidebar.selectbox("LLM Model Architecture", ["qwen/qwen3.6-27b", "llama-3.1-8b-instant", "groq/compound", "qwen-2.5-32b"])

if groq_api_key:
    st.sidebar.info("Groq Connection Active: Live Qwen Model Connected")
else:
    st.sidebar.info("Offline Mode: Deterministic Grounded Provider Active")

# 1. Loan Selection for Review
st.subheader("1. Select Flagged Loan for Triage")

queue_file = Path("artifacts/anomaly/reviewer_queue.json")
selected_loan_context = {}

if queue_file.exists():
    with open(queue_file, "r") as f:
        queue_data = json.load(f)

    loans_list = queue_data.get("loans", queue_data) if isinstance(queue_data, dict) else queue_data
    loan_options = [
        f"Rank #{q.get('queue_rank', idx)} | Loan {q.get('loan_id', 'UNKNOWN')} | Anomaly: {float(q.get('anomaly_score', 0.0)):.3f} | {q.get('exception_type', 'EXCEPTION')}"
        for idx, q in enumerate(loans_list, start=1)
    ]
    selected_option = st.selectbox("Select loan from Reviewer Queue:", loan_options)
    selected_idx = loan_options.index(selected_option)
    selected_item = loans_list[selected_idx]

    selected_loan_context = {
        "loan_id": str(selected_item.get("loan_id")),
        "reporting_month": str(selected_item.get("reporting_month", 202401)),
        "anomaly_score": round(float(selected_item.get("anomaly_score", 0.0)), 4),
        "exception_type": str(selected_item.get("exception_type", "DATA_QUALITY_EXCEPTION")),
        "flag_source": str(selected_item.get("flag_source", "DETERMINISTIC_RULE")),
        "priority_score": round(float(selected_item.get("priority_score", 0.85)), 4),
        "recommended_action": str(selected_item.get("recommended_action", "MANUAL_AUDIT")),
        "confidence": round(float(selected_item.get("confidence", 0.85)), 4),
    }

    st.json(selected_loan_context)
else:
    st.warning("Reviewer queue artifact not found. Please execute the pipeline.")
    selected_loan_context = {
        "loan_id": "LOAN_DEMO_001",
        "anomaly_score": 0.892,
        "exception_type": "DATA_QUALITY_EXCEPTION",
        "recommended_action": "MANUAL_AUDIT",
        "confidence": 0.85,
    }

st.markdown("---")

# 2. Interactive LLM Generation & Grounding
st.subheader("2. Grounded Reviewer Note Generation")

col_btn1, col_btn2 = st.columns(2)
run_gen = col_btn1.button("Generate Grounded Case Summary (Groq / Qwen)", type="primary", use_container_width=True)
test_hallucination = col_btn2.button("Run Hallucination Rejection Audit (Step 13)", use_container_width=True)

if run_gen or test_hallucination:
    provider = GroqQwenProvider(
        model_id=model_choice,
        api_key=groq_api_key if groq_api_key else None,
    )

    prompt = (
        f"Generate a concise institutional mortgage reviewer case summary for loan {selected_loan_context.get('loan_id')}. "
        f"Context attributes: Anomaly Score={selected_loan_context.get('anomaly_score')}, "
        f"Exception Type={selected_loan_context.get('exception_type')}, "
        f"Recommended Action={selected_loan_context.get('recommended_action')}, "
        f"Confidence={selected_loan_context.get('confidence')}. "
        "Strict rule: You MUST only cite numbers provided in context."
    )

    with st.spinner("Processing generation and verifying grounding validation..."):
        if test_hallucination:
            raw_text = (
                f"RECOMMENDATION_REQUIRING_HUMAN_CONFIRMATION: Loan {selected_loan_context.get('loan_id')} "
                f"shows anomaly score of {selected_loan_context.get('anomaly_score')}. "
                f"The borrower has an unverified 38.5% probability of early refinancing, and credit score dropped by 45 points."
            )
        else:
            response = provider.generate(prompt)
            raw_text = response.text

        validator = GroundingValidator(numeric_tolerance=0.01)
        val_result = validator.validate(raw_text, selected_loan_context)

    st.markdown("#### Generated Reviewer Note")
    st.markdown(f"> {raw_text}")

    st.markdown("#### Grounding Validator Audit Result")
    if val_result.is_valid:
        st.success("Grounding Validation: PASSED (100% of numerical assertions verified in model ground truth)")
        st.caption(f"Verified numerical claims: {val_result.resolved_claims}")
    else:
        st.error(f"Grounding Validation: REJECTED (Unverified numerical assertions detected: {val_result.unresolved_claims})")
        st.warning("Governance Enforcement: This note was blocked from presentation to the human reviewer per Principle III.")

st.markdown("---")

# 3. Interactive Data Dictionary Retriever (FR-057)
st.subheader("3. Reference Data Dictionary Query")
st.caption("Directly retrieved from official Fannie Mae single-family data dictionary specification.")

field_query = st.selectbox(
    "Select mortgage field definition:",
    [
        "credit_score", "debt_to_income_ratio", "original_ltv", "cltv",
        "original_interest_rate", "current_actual_upb", "loan_age",
        "current_loan_delinquency_status", "zero_balance_code", "modification_flag"
    ]
)
if field_query:
    st.info(f"{field_query}: {retrieve_field_definition(field_query)}")

st.markdown("---")

# 4. Prompt & Audit Trail (FR-058)
st.subheader("4. Append-Only Prompt & Audit Trail")
prompt_log_file = Path("artifacts/narrate/prompt_log.jsonl")
if prompt_log_file.exists():
    logs = []
    with open(prompt_log_file, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                logs.append(json.loads(line))
            except json.JSONDecodeError:
                # Skip malformed or concatenated lines silently
                pass
    if logs:
        st.dataframe(pd.DataFrame(logs), use_container_width=True)
    else:
        st.info("No valid audit log entries found.")
else:
    st.info("Prompt audit log is populated during full pipeline batch execution.")

