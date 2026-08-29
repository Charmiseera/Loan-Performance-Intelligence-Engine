# Tasks: Advanced Intelligence Suite

**Feature**: `specs/002-advanced-features`  
**Governing Document**: `.specify/memory/constitution.md`

## Phase 1: Setup & Foundational

- [x] T001 Setup advanced module directories in `src/lpie/advanced/` and `src/lpie/explain/`
- [x] T002 [P] Create base schemas and data contracts in `specs/002-advanced-features/contracts/`

---

## Phase 2: User Story 1 - Portfolio Monte Carlo Loss & Prepayment Simulation (Priority: P1) 🎯 MVP

**Goal**: Vectorized 10,000-path stochastic loss and prepayment cash-flow simulation computing 95%/99% VaR and Expected Shortfall (CVaR).

- [x] T003 [P] [US1] Implement unit tests for Monte Carlo simulation bounds in `tests/unit/test_monte_carlo.py`
- [x] T004 [US1] Implement vectorized Monte Carlo simulator in `src/lpie/advanced/monte_carlo.py`
- [x] T005 [US1] Integrate Monte Carlo portfolio simulation into `src/lpie/stages/scenario.py` emitting `artifacts/scenario/monte_carlo_results.json`

---

## Phase 3: User Story 2 - Subgroup Calibration & Fairness Parity Audit (Priority: P1)

**Goal**: Evaluate Brier Score and ECE across credit tiers (Subprime, Near-Prime, Prime), vintages, and demographic proxies, computing Disparate Impact and Equalized Odds differences.

- [x] T006 [P] [US2] Implement unit tests for subgroup calibration and fairness parity in `tests/unit/test_fairness.py`
- [x] T007 [US2] Implement subgroup fairness & calibration analyzer in `src/lpie/advanced/fairness.py`
- [x] T008 [US2] Integrate fairness audit report emission into `src/lpie/stages/report.py` emitting `artifacts/reports/fairness_audit_report.json`

---

## Phase 4: User Story 3 - Counterfactual Explanations & What-If Credit Sensitivity (Priority: P2)

**Goal**: Sparse coordinate descent optimization computing actionable loan-level perturbations to reduce predicted default probability below target thresholds while preserving immutable characteristics.

- [x] T009 [P] [US3] Implement unit tests for counterfactual search and immutable preservation in `tests/unit/test_counterfactual.py`
- [x] T010 [US3] Implement sparse counterfactual optimizer in `src/lpie/explain/counterfactual.py`
- [x] T011 [US3] Integrate counterfactual recommendation generator into `src/lpie/stages/explain.py`

---

## Phase 5: User Story 4 - High-Resolution Drift Monitoring & Alerting (Priority: P2)

**Goal**: Compute PSI, Kolmogorov-Smirnov statistics, and Wasserstein distance across all 66 origination and performance features, categorizing features into Green/Yellow/Red drift alert tiers.

- [x] T012 [P] [US4] Implement unit tests for high-resolution drift metrics in `tests/unit/test_drift_monitor.py`
- [x] T013 [US4] Implement multi-feature drift monitor in `src/lpie/advanced/drift_monitor.py`
- [x] T014 [US4] Integrate drift monitor output into `src/lpie/stages/profile.py`

---

## Phase 6: User Story 5 - Epistemic & Aleatoric Uncertainty Quantification (Priority: P3)

**Goal**: Compute 90% prediction confidence intervals ($[p_{05}, p_{95}]$) for all four prediction horizons using GBDT leaf path ensemble variance.

- [x] T015 [P] [US5] Implement unit tests for prediction confidence intervals in `tests/unit/test_uncertainty_bounds.py`
- [x] T016 [US5] Implement interval estimation in `src/lpie/models/uncertainty.py`
- [x] T017 [US5] Integrate uncertainty columns into `src/lpie/stages/train.py`

---

## Phase 7: Polish, Dashboard UI & End-to-End Verification

- [x] T018 [P] Add Monte Carlo loss distribution & VaR percentiles to `app/pages/5_Scenarios.py`
- [x] T019 [P] Add Counterfactual what-if loan calculator to `app/pages/6_Explainability.py`
- [x] T020 [P] Add Subgroup Fairness Parity & Calibration curves to `app/pages/2_Predictions.py`
- [x] T021 Run full end-to-end pipeline execution and verify 100% test pass rate across all test suites
