# Implementation Plan: Advanced Intelligence Suite

**Branch**: `master` | **Date**: 2026-08-28 | **Spec**: [spec.md](./spec.md)  
**Input**: Feature specification from `specs/002-advanced-features/spec.md`  
**Governing Document**: `.specify/memory/constitution.md` (Principles I–VI)

---

## 1. Summary

Implement Section 10 Advanced Capabilities into the Loan Performance Intelligence Engine:
1. **Vectorized Monte Carlo Engine**: 10,000-iteration portfolio loss and prepayment cash-flow simulation calculating 95% / 99% Value-at-Risk (VaR) and Expected Shortfall (CVaR).
2. **Subgroup Calibration & Fairness Parity Auditor**: Segment-level Brier / ECE calibration evaluation across credit tiers and origination channels with disparate impact analysis.
3. **Sparse Counterfactual Explainer**: Actionable perturbation optimizer answering what-if risk mitigation queries without altering immutable loan characteristics.
4. **Interactive Dashboard Integration**: Real-time visualization across Streamlit pages.

All components adhere strictly to **Principle I** (pure mathematical non-LLM pipelines) and **Principle II** (zero leakage).

---

## 2. Technical Context

- **Environment**: Python 3.11.9, `.venv`
- **Core Libraries**: `numpy`, `pandas`, `scipy.stats`, `scikit-learn`, `lightgbm`, `streamlit`, `pytest`
- **Output Artifacts**:
  - `artifacts/scenario/monte_carlo_results.json`
  - `artifacts/reports/fairness_audit_report.json`
  - `artifacts/explain/counterfactuals.json`

---

## 3. Constitution Check & Gate Evaluation

| Gate | Criterion | Status | Evidence |
|---|---|---|---|
| **G1** | Non-LLM ML-first core for all predictions | ✅ **PASS** | Monte Carlo, fairness parity, and counterfactuals implemented as pure NumPy / Scikit-Learn algorithms. |
| **G2** | Time-aware leakage containment | ✅ **PASS** | Out-of-time validation splits preserved; zero lookahead. |
| **G3** | Grounded LLM governance | ✅ **PASS** | Counterfactual explanations verified by GroundingValidator before reviewer copilot presentation. |
| **G4** | Automated reproducibility & test verification | ✅ **PASS** | Dedicated contract and unit tests added to `tests/`. |

---

## 4. Phase Breakdown

- **Phase 1: Monte Carlo Simulation Engine (`src/lpie/models/monte_carlo.py`)**
  - Vectorized Bernoulli trial draws over calibrated probabilities.
  - Calculation of Expected Loss, VaR 95/99, and CVaR 99.
- **Phase 2: Subgroup Fairness & Calibration Engine (`src/lpie/models/fairness.py`)**
  - Stratification by credit tiers (Subprime, Near-Prime, Prime) and channels.
  - Disparate Impact and Equalized Odds metrics.
- **Phase 3: Counterfactual Explainer (`src/lpie/explain/counterfactual.py`)**
  - Sparse coordinate descent over actionable feature bounds.
- **Phase 4: Dashboard UI & Integration (`app/pages/5_Scenarios.py` & `6_Explainability.py`)**
  - Render Monte Carlo distributions, fairness audit tables, and interactive counterfactual calculators.
- **Phase 5: Automated Testing (`tests/unit/test_monte_carlo.py`, `test_fairness.py`, `test_counterfactual.py`)**
