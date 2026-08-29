import json
from pathlib import Path
import pandas as pd
import pytest
from lpie.conf.validator import validate_submission_file


def test_submission_contract_schema_valid():
    schema_path = Path("specs/001-loan-performance-intelligence/contracts/submission_schema.json")
    assert schema_path.exists(), "Submission schema contract must exist"
    with open(schema_path, "r", encoding="utf-8") as f:
        schema = json.load(f)
    assert "required" in schema
    assert "properties" in schema
    
    # Must specify key columns
    req = schema["required"]
    for col in [
        "loan_id",
        "reporting_month",
        "next_3m_delinquency_prob",
        "next_6m_delinquency_prob",
        "next_12m_default_prob",
        "next_12m_prepayment_prob",
        "next_state",
        "anomaly_score",
        "exception_required",
        "exception_type",
        "top_drivers",
        "recommended_action",
        "confidence",
    ]:
        assert col in req, f"Column {col} must be in submission schema required list"


def test_validate_submission_file_on_valid_synthetic_df(tmp_path):
    sub_path = tmp_path / "submission.csv"
    schema_path = Path("specs/001-loan-performance-intelligence/contracts/submission_schema.json")
    
    valid_df = pd.DataFrame({
        "loan_id": ["L001", "L002"],
        "reporting_month": [202306, 202306],
        "next_3m_delinquency_prob": [0.05, 0.85],
        "next_6m_delinquency_prob": [0.08, 0.90],
        "next_12m_default_prob": [0.01, 0.65],
        "next_12m_prepayment_prob": [0.15, 0.02],
        "next_state": ["CURRENT", "30_DAYS_DELINQUENT"],
        "anomaly_score": [0.12, 0.78],
        "exception_required": [False, True],
        "exception_type": ["NONE", "DELINQUENCY_ACCELERATION"],
        "top_drivers": ["credit_score=750; ltv=70", "delinq_max_6m=3; dti=55"],
        "recommended_action": ["MONITOR", "SERVICER_OUTREACH"],
        "confidence": [0.95, 0.88],
    })
    valid_df.to_csv(sub_path, index=False)
    
    exit_code = validate_submission_file(str(sub_path), str(schema_path))
    assert exit_code == 0
