from lpie.survival.incidence import compute_cumulative_incidence_functions


def test_cif_bounds_sum_to_le_one():
    # Test that default and prepayment cumulative incidence sum to <= 1.0 at every horizon (SC-012)
    dummy_hazards = {
        "time_points": list(range(1, 13)),
        "hazard_default": [0.02] * 12,
        "hazard_prepay": [0.08] * 12,
        "at_risk": [1000 - i * 50 for i in range(12)],
    }

    cif_res = compute_cumulative_incidence_functions(dummy_hazards)
    assert cif_res["bounds_validated"] is True
    assert len(cif_res["cif_default"]) == 12
    assert len(cif_res["cif_prepay"]) == 12

    for d, p in zip(cif_res["cif_default"], cif_res["cif_prepay"]):
        assert d >= 0.0
        assert p >= 0.0
        assert (d + p) <= 1.00001
