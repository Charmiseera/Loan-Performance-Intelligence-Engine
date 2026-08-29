import numpy as np
import pandas as pd
import pytest
from lpie.features.asof import build_asof_features_for_loan
from lpie.features.registry import FeatureRegistry, FeatureSpec


def test_target_name_screening_in_features():
    """Verify that forbidden outcome target names are screened out of feature specifications."""
    forbidden = {
        "prob_deterioration_3m",
        "prob_deterioration_6m",
        "prob_default_12m",
        "prob_prepay_12m",
        "zero_balance_code",
        "actual_loss",
        "target_deterioration_3m",
        "target_deterioration_6m",
        "target_default_12m",
        "target_prepay_12m",
    }
    
    registry = FeatureRegistry()
    registry.register(FeatureSpec(name="credit_score", window=(0, 0)))
    registry.register(FeatureSpec(name="delinq_max_6m", window=(-6, 0)))
    
    # Attempting to register a forward looking or target feature must raise ValueError
    with pytest.raises(ValueError, match="Forward-looking"):
        registry.register(FeatureSpec(name="future_delinq", window=(0, 3)))
        
    for feat in registry.list_features():
        assert feat.name not in forbidden


def test_future_perturbation_invariance():
    """
    Empirical Leakage Guard:
    Perturbing panel rows strictly after as-of month M must leave the feature matrix at month M byte-identical.
    """
    loan_history_orig = pd.DataFrame({
        "loan_id": ["L001"] * 6,
        "monthly_reporting_period": [202001, 202002, 202003, 202004, 202005, 202006],
        "current_actual_upb": [100000.0, 99000.0, 98000.0, 97000.0, 96000.0, 95000.0],
        "delinquency_status_num": [0.0, 0.0, 0.0, 0.0, 1.0, 2.0],
        "current_interest_rate": [4.5] * 6,
    })
    
    # Compute features as of month 202003
    asof_month = 202003
    feats_1 = build_asof_features_for_loan(loan_history_orig, asof_month)
    
    # Perturb rows after 202003 (e.g. 202004, 202005, 202006)
    loan_history_perturbed = loan_history_orig.copy()
    loan_history_perturbed.loc[loan_history_perturbed["monthly_reporting_period"] > asof_month, "delinquency_status_num"] = 99.0
    loan_history_perturbed.loc[loan_history_perturbed["monthly_reporting_period"] > asof_month, "current_actual_upb"] = 0.0
    
    feats_2 = build_asof_features_for_loan(loan_history_perturbed, asof_month)
    
    pd.testing.assert_series_equal(feats_1, feats_2)
