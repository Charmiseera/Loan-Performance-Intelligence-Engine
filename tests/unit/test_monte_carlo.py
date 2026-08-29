import numpy as np
import pytest
from lpie.advanced.monte_carlo import simulate_portfolio_monte_carlo


def test_monte_carlo_simulation_bounds():
    np.random.seed(42)
    n_loans = 1000
    upb = np.full(n_loans, 200000.0)
    p_def = np.full(n_loans, 0.03)
    p_prep = np.full(n_loans, 0.15)

    res = simulate_portfolio_monte_carlo(
        upb_array=upb,
        prob_default_array=p_def,
        prob_prepay_array=p_prep,
        num_iterations=500,
        lgd_mean=0.35,
        random_seed=42,
    )

    assert res["num_iterations"] == 500
    assert res["total_active_loans"] == 1000
    assert res["total_active_upb"] == 200000000.0
    assert 0 <= res["var_95"] <= res["var_99"] <= res["total_active_upb"]
    assert res["cvar_99"] >= res["var_99"]
    assert res["expected_loss"] > 0
    assert res["prepayment_cashflow_std"] >= 0
