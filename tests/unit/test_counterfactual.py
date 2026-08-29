import pytest
from lpie.explain.counterfactual import generate_sparse_counterfactual


def test_counterfactual_immutable_preservation():
    loan_profile = {
        "loan_id": "LOAN_TEST_99",
        "credit_score": 640.0,
        "original_upb": 280000.0,
        "current_actual_upb": 265000.0,
        "original_dti": 45.0,
        "rate_spread_incentive": 1.25,
        "first_payment_date": 202001,
        "property_state": "CA",
    }

    cf = generate_sparse_counterfactual(
        loan_profile=loan_profile,
        baseline_prob=0.18,
        target_prob=0.04,
    )

    assert cf["loan_id"] == "LOAN_TEST_99"
    assert cf["baseline_default_prob"] == 0.18
    assert cf["target_default_prob"] == 0.04
    assert "actionable_perturbations" in cf
    assert cf["immutable_features_preserved"] is True
    # Verify immutable features were NOT modified
    assert "property_state" not in cf["actionable_perturbations"]
    assert "first_payment_date" not in cf["actionable_perturbations"]
