from typing import Any, Dict, List
import numpy as np


def compute_cumulative_incidence_functions(
    hazards_data: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Computes Cumulative Incidence Functions (CIF) for competing risks (Default vs Prepayment)
    using the discrete Aalen-Johansen formula (FR-038, FR-039, SC-012).

    S(t-1) = Overall overall survival probability up to t-1
    CIF_k(t) = CIF_k(t-1) + S(t-1) * h_k(t)
    S(t) = S(t-1) * (1 - (h_def(t) + h_prep(t)))

    Guarantees: CIF_default(t) + CIF_prepay(t) <= 1.0 for all t (SC-012).
    """
    time_points = hazards_data.get("time_points", [])
    h_def_list = hazards_data.get("hazard_default", [])
    h_prep_list = hazards_data.get("hazard_prepay", [])
    at_risk_list = hazards_data.get("at_risk", [])

    cif_default: List[float] = []
    cif_prepay: List[float] = []
    overall_survival: List[float] = []

    current_cif_def = 0.0
    current_cif_prep = 0.0
    current_s = 1.0

    for t, h_def, h_prep in zip(time_points, h_def_list, h_prep_list):
        total_hazard = min(1.0, h_def + h_prep)
        inc_def = current_s * h_def
        inc_prep = current_s * h_prep

        current_cif_def += inc_def
        current_cif_prep += inc_prep

        # Bound check (SC-012)
        if current_cif_def + current_cif_prep > 1.0:
            scale = 1.0 / (current_cif_def + current_cif_prep)
            current_cif_def *= scale
            current_cif_prep *= scale

        current_s = max(0.0, current_s * (1.0 - total_hazard))

        cif_default.append(round(current_cif_def, 5))
        cif_prepay.append(round(current_cif_prep, 5))
        overall_survival.append(round(current_s, 5))

    return {
        "time_points": time_points,
        "cif_default": cif_default,
        "cif_prepay": cif_prepay,
        "overall_survival": overall_survival,
        "at_risk": at_risk_list,
        "bounds_validated": all(
            (d + p) <= 1.00001 for d, p in zip(cif_default, cif_prepay)
        ),
    }
