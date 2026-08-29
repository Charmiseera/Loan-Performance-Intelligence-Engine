import pandas as pd
import numpy as np
from lpie.data.rule_evaluator import evaluate_cross_column_rules


def test_evaluate_cross_column_rules_detects_violations():
    df = pd.DataFrame({
        "maturity_date": [203001, 201001],
        "origination_date": [202001, 202001], # Second row has maturity before origination
        "cltv": [80.0, 70.0],
        "original_ltv": [80.0, 90.0], # Second row has CLTV < LTV
        "debt_to_income_ratio": [35.0, 150.0], # Second row has DTI > 100
        "original_interest_rate": [4.5, -1.0], # Second row has negative interest rate
    })

    results = evaluate_cross_column_rules(df)
    assert "RULE_MATURITY_AFTER_ORIGINATION" in results
    assert results["RULE_MATURITY_AFTER_ORIGINATION"]["violation_count"] == 1

    assert "RULE_CLTV_GE_LTV" in results
    assert results["RULE_CLTV_GE_LTV"]["violation_count"] == 1

    assert "RULE_DTI_BOUNDS" in results
    assert results["RULE_DTI_BOUNDS"]["violation_count"] == 1

    assert "RULE_INTEREST_RATE_BOUNDS" in results
    assert results["RULE_INTEREST_RATE_BOUNDS"]["violation_count"] == 1
