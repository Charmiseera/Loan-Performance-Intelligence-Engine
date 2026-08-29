# Tasks: Loan Performance Intelligence Engine

**Input**: Design documents from `/specs/001-loan-performance-intelligence/` (`spec.md`, `plan.md`, `research.md`, `contracts/`)
**Governing Document**: `.specify/memory/constitution.md` v1.0.1
**Tests**: MANDATORY per spec §Testing Requirement and FR-069 through FR-074.

## Format: `- [ ] [TaskID] [P?] [Story?] Description with file path`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: User story identifier (`[US1]` through `[US8]`) for story-specific phases
- Every task includes explicit target file paths

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project layout, package configuration, configuration schemas, and base utility modules.

- [x] T001 Create project package directory structure per plan in `src/lpie/`, `config/`, `templates/`, `tests/`, `app/`
- [x] T002 Create root seed and child-seed derivation utility in `src/lpie/util/seed.py`
- [x] T003 [P] Create structured logging utility in `src/lpie/util/logging.py`
- [x] T004 [P] Create configuration models and dataclasses in `src/lpie/conf/models.py`
- [x] T005 Create typed YAML configuration loader with strict validation in `src/lpie/conf/loader.py`
- [x] T006 [P] Create pipeline configuration files in `config/pipeline.yaml`, `config/schema_r47.yaml`, `config/field_mapping.yaml`, `config/splits.yaml`, `config/features.yaml`, `config/scenarios.yaml`, `config/llm.yaml`, `config/validation_rules.json`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core data layer, artifact store, stage registry, base contracts, and synthetic test fixture harness that MUST be complete before user stories can run.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [x] T007 Create synthetic mini-panel test fixture generator in `tests/fixtures/make_tiny_panel.py` and configure `tests/conftest.py`
- [x] T008 [P] Create unit test for child-seed derivation in `tests/unit/test_seed_derivation.py`
- [x] T009 [P] Create deterministic artifact storage manager (Parquet/JSON/JSONL/Markdown with sorted keys) in `src/lpie/store/store.py`
- [x] T010 [P] Create run manifest manager (recording config hash, seed, library versions, hardware, stage timings) in `src/lpie/store/manifest.py`
- [x] T011 [P] Create per-field missingness and sentinel handler in `src/lpie/data/sentinels.py`
- [x] T012 [P] Create unit test for per-field sentinel policies in `tests/unit/test_sentinels.py`
- [x] T013 [P] Create categorical value decoder in `src/lpie/data/decode.py`
- [x] T014 [P] Create contract test verifying schema config matches documented R47 layout in `tests/contract/test_schema_config_matches_layout.py`
- [x] T015 Create chunked pipe-delimited streaming data reader with schema dtypes in `src/lpie/data/reader.py`
- [x] T016 Create two-level stratified whole-loan sampler with recorded sampling weights in `src/lpie/data/sample.py`
- [x] T017 Create stage abstraction protocol (declared input/output artifacts) in `src/lpie/stages/base.py`
- [x] T018 Create stage graph registry with topological sorting and transitive closure analysis in `src/lpie/stages/registry.py`
- [x] T019 Create CLI entrypoint and command runner (`run`, `stage`, `validate`) in `src/lpie/cli.py` and `src/lpie/__main__.py`

**Checkpoint**: Core data reading, configuration, storage, and stage execution engine are verified ready.

---

## Phase 3: User Story 1 - A Complete, Submittable Baseline (Priority: P1) 🎯 MVP

**Goal**: Deliver a working, deterministic end-to-end P1 vertical slice across all stages producing a valid `submission.csv`, metrics, basic profiling, baseline predictions, anomaly score, explanations, reviewer note, and model card in one command.

**Independent Test**: Running `python -m lpie run --config config/pipeline.yaml` against raw data executes all stages end-to-end, passes `contracts/submission_schema.json` schema validation, achieves byte-identical outputs across repeated seeded runs, and runs successfully with the LLM disabled.

### Tests for User Story 1

- [ ] T020 [P] [US1] Create submission contract validation test against schema in `tests/contract/test_submission_contract.py` (FR-072)
- [ ] T021 [P] [US1] Create static graph assertion verifying no LLM artifact on submission path in `tests/unit/test_no_llm_on_submission_path.py` (Principle I)
- [ ] T022 [P] [US1] Create temporal split disjointness and embargo unit test in `tests/unit/test_split_disjointness.py` (FR-070)
- [ ] T023 [P] [US1] Create leakage guard test (target exclusion and future perturbation test) in `tests/unit/test_leakage_guard.py` (FR-069)
- [ ] T024 [P] [US1] Create end-to-end pipeline execution test with synthetic fixture in `tests/integration/test_pipeline_end_to_end.py`
- [ ] T025 [P] [US1] Create seeded pipeline determinism and byte-identical output test in `tests/integration/test_determinism.py` (FR-071)
- [ ] T026 [P] [US1] Create offline pipeline execution test with LLM provider disabled in `tests/integration/test_pipeline_without_llm.py` (FR-073)

### Implementation for User Story 1

- [ ] T027 [US1] Implement Ingest stage (chunked read + stratified loan sampling -> raw parquet) in `src/lpie/stages/ingest.py`
- [ ] T028 [US1] Implement Contract stage (structural schema validation and quarantine tracking) in `src/lpie/stages/contract.py`
- [ ] T029 [US1] Implement Zero-Balance code mapping and termination label builder in `src/lpie/labels/termination.py` and `tests/unit/test_termination_mapping.py`
- [ ] T030 [US1] Implement horizon-based outcome target definitions (3m/6m deterioration, 12m default, 12m prepayment, next_state) in `src/lpie/labels/outcomes.py`
- [ ] T031 [US1] Implement Label stage materializing target outcomes in `src/lpie/stages/label.py`
- [ ] T032 [US1] Implement Split stage (temporal windows, embargo gap, leakage audit artifact) in `src/lpie/stages/split.py`
- [ ] T033 [US1] Implement as-of-month feature registry and strict forward-window validator in `src/lpie/features/registry.py` and `src/lpie/features/asof.py`
- [ ] T034 [US1] Implement static origination and panel lag/rolling feature builders in `src/lpie/features/static.py` and `src/lpie/features/panel.py`
- [ ] T035 [US1] Implement Features stage generating split-aligned matrices in `src/lpie/stages/features.py`
- [ ] T036 [US1] Implement baseline logistic regression / class-frequency models in `src/lpie/models/baseline.py`
- [ ] T037 [US1] Implement classification metrics (PR-AUC, recall@precision, Brier, denominator tracking) in `src/lpie/models/metrics.py`
- [ ] T038 [US1] Implement GBDT classifiers (LightGBM/XGBoost) with post-hoc calibration in `src/lpie/models/gbdt.py` and `src/lpie/models/calibration.py`
- [ ] T039 [US1] Implement next-state multinomial classifier in `src/lpie/models/multistate.py`
- [ ] T040 [US1] Implement Train stage executing baselines, primary models, calibration, and metrics logging in `src/lpie/stages/train.py`
- [ ] T041 [US1] Implement deterministic rule engine and IsolationForest anomaly scorer in `src/lpie/anomaly/rules.py` and `src/lpie/anomaly/learned.py`
- [ ] T042 [US1] Implement rule-statistical anomaly fusion and action decision table in `src/lpie/anomaly/combine.py` and `src/lpie/anomaly/actions.py`
- [ ] T043 [US1] Implement Anomaly stage generating anomaly scores, exception flags, and actions in `src/lpie/stages/anomaly.py`
- [ ] T044 [US1] Implement confidence and uncertainty estimation in `src/lpie/models/uncertainty.py`
- [ ] T045 [US1] Implement TreeSHAP global importance and local attribution in `src/lpie/explain/global_importance.py` and `src/lpie/explain/local_attribution.py`
- [ ] T046 [US1] Implement Explain stage writing feature attribution artifacts in `src/lpie/stages/explain.py`
- [ ] T047 [US1] Implement abstract LLM provider and deterministic offline fallback in `src/lpie/llm/provider.py` and `src/lpie/llm/offline_provider.py`
- [ ] T048 [US1] Implement append-only prompt logger with recommendation stamping in `src/lpie/llm/promptlog.py`
- [ ] T049 [US1] Implement Narrate stage writing reviewer case summary notes in `src/lpie/stages/narrate.py`
- [ ] T050 [US1] Implement Jinja2 report templates (`templates/model_card.md.j2`, `templates/data_intelligence_report.md.j2`, `templates/explainability_report.md.j2`, `templates/scenario_report.md.j2`) and sourcing contract test in `tests/contract/test_report_numbers_are_sourced.py`
- [ ] T051 [US1] Implement Report stage reading per-stage JSON metrics to render markdown deliverables in `src/lpie/stages/report.py`
- [ ] T052 [US1] Implement Submit stage assembling and validating `submission.csv` against JSON schema in `src/lpie/stages/submit.py`

**Checkpoint**: Full end-to-end P1 pipeline executes cleanly from a single command, producing valid `submission.csv` and all foundational reports.

---

## Phase 4: User Story 2 - Trustworthy Data Before Any Model (Priority: P2)

**Goal**: Deliver deep data intelligence and profiling (15 points) — distributions, missingness patterns, sentinel value audits, cross-column validation rules, correlation/dependency analysis, population drift measurement, and multi-component record/batch quality scoring.

**Independent Test**: Run `python -m lpie stage profile` against raw data. Output report documents identified disguised sentinels, rule violation counts with offending IDs, PSI/KS drift rankings between training and scoring windows, and inspectable quality score breakdowns.

### Tests for User Story 2

- [ ] T053 [P] [US2] Create data profiling and distribution statistics unit test in `tests/unit/test_profiling_stats.py`
- [ ] T054 [P] [US2] Create cross-column consistency rules unit test in `tests/unit/test_validation_rules.py`
- [ ] T055 [P] [US2] Create population drift (PSI / KS) calculation unit test in `tests/unit/test_drift_metrics.py`

### Implementation for User Story 2

- [ ] T056 [US2] Implement comprehensive column statistics and missingness pattern detector in `src/lpie/data/profile_stats.py`
- [ ] T057 [US2] Implement deterministic cross-column business rule evaluators (dates, balance monotonicity, modification consistency) in `src/lpie/data/rule_evaluator.py`
- [ ] T058 [US2] Implement population drift calculator (PSI, Wasserstein / Kolmogorov-Smirnov) comparing train vs scoring splits in `src/lpie/data/drift.py`
- [ ] T059 [US2] Implement multi-component record-level and batch-level quality scoring model in `src/lpie/data/quality_score.py`
- [ ] T060 [US2] Implement Profile stage emitting `artifacts/profile/data_intelligence_report.md` and `artifacts/profile/profile_metrics.json` in `src/lpie/stages/profile.py`
- [ ] T061 [US2] Implement Streamlit Data Intelligence view in `app/pages/1_Data_Intelligence.py`

**Checkpoint**: Data Intelligence stage fully functional with detailed reporting, drift ranking, and interactive UI visualizer.

---

## Phase 5: User Story 3 - Multi-Outcome Prediction That Survives Scrutiny (Priority: P2)

**Goal**: Deliver rigorous predictive modeling (20 points) — calibrated probabilities for 3m/6m deterioration, 12m default, 12m prepayment, and next_state, with honest class imbalance handling, baseline comparisons, and reliability curve analysis.

**Independent Test**: Evaluate trained baseline vs improved models on out-of-time test split. Generate reliability diagrams, Brier score decompositions, and PR curves showing demonstrable lift over baselines while preserving natural calibration.

### Tests for User Story 3

- [ ] T062 [P] [US3] Create model calibration and reliability calculation unit test in `tests/unit/test_calibration.py`
- [ ] T063 [P] [US3] Create multi-class next-state evaluation metric test in `tests/unit/test_multistate_metrics.py`
- [ ] T064 [P] [US3] Create naturally-weighted evaluation holdout test in `tests/unit/test_natural_weight_eval.py`

### Implementation for User Story 3

- [ ] T065 [US3] Implement hyperparameter tuning and cross-validation across time splits in `src/lpie/models/tuning.py`
- [ ] T066 [US3] Implement isotonic regression and Platt scaling calibrators on naturally-weighted holdout in `src/lpie/models/calibration.py`
- [ ] T067 [US3] Implement model comparison suite (baseline vs improved GBDT per outcome) in `src/lpie/models/compare.py`
- [ ] T068 [US3] Implement reliability diagram generator and calibration error (ECE/MCE) reporter in `src/lpie/models/reliability.py`
- [ ] T069 [US3] Update Train stage to log model comparison tables, PR curves, and reliability artifacts in `src/lpie/stages/train.py`
- [ ] T070 [US3] Implement Streamlit Predictions and Model Performance view in `app/pages/2_Predictions.py`

**Checkpoint**: Multi-outcome models calibrated, benchmarked against baselines, and visualized with reliability curves.

---

## Phase 6: User Story 4 - Time-to-Event With Competing Risks (Priority: P3)

**Goal**: Deliver survival analysis and transition modeling (15 points) — cause-specific hazard models (default vs prepayment), cumulative incidence functions (CIF) respecting competing risks, censoring handling, and comparison against static models.

**Independent Test**: Fit competing-risk models on loan panels with right-censoring; verify cumulative incidence curves for default and prepayment do not exceed 1.0; verify censored loans exit the risk set appropriately; compare against non-survival baseline.

### Tests for User Story 4

- [ ] T071 [P] [US4] Create cause-specific hazard and right-censoring handling unit test in `tests/unit/test_survival_hazard.py`
- [ ] T072 [P] [US4] Create cumulative incidence function (CIF) bounds and non-divergence unit test in `tests/unit/test_cif_bounds.py`

### Implementation for User Story 4

- [ ] T073 [US4] Implement right-censored panel dataset builder for survival analysis in `src/lpie/survival/dataset.py`
- [ ] T074 [US4] Implement cause-specific Cox / Aalen survival hazard models in `src/lpie/survival/cause_specific.py`
- [ ] T075 [US4] Implement non-parametric and model-based Cumulative Incidence Function (CIF) calculator in `src/lpie/survival/incidence.py`
- [ ] T076 [US4] Implement survival comparison against binary static classification in `src/lpie/survival/compare.py`
- [ ] T077 [US4] Implement Survival stage emitting survival curves, risk-set counts, and metrics in `src/lpie/stages/survival.py`
- [ ] T078 [US4] Implement Streamlit Time-to-Event view with dynamic CIF curves in `app/pages/3_Time_To_Event.py`

**Checkpoint**: Competing-risks survival modeling operational with cumulative incidence curves and censoring accounting.

---

## Phase 7: User Story 5 - A Reviewer Queue Worth a Reviewer's Time (Priority: P3)

**Goal**: Deliver operational anomaly and exception intelligence (10 points) — prioritized reviewer queue of 20+ records with anomaly scores, predicted exception categories, named rule/statistical contributing drivers, and constructed reconciliation fixture.

**Independent Test**: Generate reviewer queue from scored data; verify at least 20 entries sorted by priority; verify each entry separates deterministic rule flags from statistical oddities; verify reconciliation fixture is generated and labeled as constructed.

### Tests for User Story 5

- [ ] T079 [P] [US5] Create reviewer queue sorting and priority ranking unit test in `tests/unit/test_queue_ranking.py`
- [ ] T080 [P] [US5] Create constructed reconciliation fixture generator validation test in `tests/unit/test_reconciliation_fixture.py`

### Implementation for User Story 5

- [ ] T081 [US5] Implement servicer-conflict reconciliation fixture generator (labeled constructed) in `src/lpie/anomaly/reconciliation.py`
- [ ] T082 [US5] Implement supervised exception category classifier in `src/lpie/anomaly/exception_classifier.py`
- [ ] T083 [US5] Implement priority ranking engine weighting rule severity, anomaly score, and loan balance in `src/lpie/anomaly/queue.py`
- [ ] T084 [US5] Update Anomaly stage to output prioritized 20+ item reviewer queue artifact in `src/lpie/stages/anomaly.py`
- [ ] T085 [US5] Implement Streamlit Reviewer Queue interactive triage page in `app/pages/4_Reviewer_Queue.py`

**Checkpoint**: Reviewer queue populated with 20+ detailed exception cases, driver breakdowns, and interactive triage UI.

---

## Phase 8: User Story 6 - Scenario and Stress Projection (Priority: P4)

**Goal**: Deliver portfolio scenario and stress simulation (10 points) — baseline, adverse credit stress, and elevated prepayment scenarios across vintages, credit bands, geography, and servicers, with waterfall driver decomposition.

**Independent Test**: Run scenario engine across baseline, adverse, and high-prepayment scenarios; verify adverse shows higher credit stress and high-prepayment shows elevated prepayment; verify segment totals reconcile with portfolio projections within tolerance.

### Tests for User Story 6

- [ ] T086 [P] [US6] Create scenario macro-shift parameter application unit test in `tests/unit/test_scenario_shift.py`
- [ ] T087 [P] [US6] Create segment reconciliation and portfolio total aggregation test in `tests/unit/test_scenario_reconciliation.py`

### Implementation for User Story 6

- [ ] T088 [US6] Implement scenario definition loader and stated assumption labeler in `src/lpie/scenario/assumptions.py`
- [ ] T089 [US6] Implement macro-economic scenario shifter (rate shock, unemployment, HPI) in `src/lpie/scenario/engine.py`
- [ ] T090 [US6] Implement multi-segment aggregator (vintage, credit band, geography, servicer) and driver waterfall decomposer in `src/lpie/scenario/project.py`
- [ ] T091 [US6] Implement Scenario stage writing scenario projections and markdown report in `src/lpie/stages/scenario.py`
- [ ] T092 [US6] Implement Streamlit Scenario and Stress Simulation page in `app/pages/5_Scenarios.py`

**Checkpoint**: Stress projection engine simulates macro scenarios across portfolio slices with waterfall driver charts.

---

## Phase 9: User Story 7 - Explanations and Declared Limits (Priority: P4)

**Goal**: Deliver explainability and responsible AI artifacts (10 points) — global feature importance, local SHAP attribution per loan, prediction confidence bounds, concrete false-positive/false-negative error analysis, and honest model card.

**Independent Test**: Produce TreeSHAP global importance and local force plots for individual loans; verify attributions sum to prediction within tolerance; produce error analysis with FP and FN case studies; generate complete model card sourced from metrics artifacts.

### Tests for User Story 7

- [ ] T093 [P] [US7] Create SHAP attribution additivity and reconciliation unit test in `tests/unit/test_shap_reconciliation.py`
- [ ] T094 [P] [US7] Create error analysis categorization (FP / FN) unit test in `tests/unit/test_error_analysis.py`

### Implementation for User Story 7

- [ ] T095 [US7] Implement TreeSHAP explainer with feature clustering and dependence analysis in `src/lpie/explain/global_importance.py`
- [ ] T096 [US7] Implement local attribution generator with confidence interval derivation in `src/lpie/explain/local_attribution.py`
- [ ] T097 [US7] Implement false-positive and false-negative error analysis engine with driver breakdown in `src/lpie/explain/error_analysis.py`
- [ ] T098 [US7] Update Explain stage to output full explainability suite and error casebook in `src/lpie/stages/explain.py`
- [ ] T099 [US7] Implement Streamlit Explainability and Model Transparency view in `app/pages/6_Explainability.py`

**Checkpoint**: Complete explainability module operating with global/local SHAP, error case studies, and limitations disclosure.

---

## Phase 10: User Story 8 - A Copilot That Recommends and Never Decides (Priority: P5)

**Goal**: Deliver grounded LLM reviewer copilot (10 points) using Groq Qwen with strict hallucination validation, complete prompt logging, grounding citations against data dictionary, recommendation labeling, and failure catalog.

**Independent Test**: Generate case summary for flagged loan; verify all numeric claims resolve to grounding context; verify prompt log records input/output/tokens/verdict; inject fabricated number and verify grounding validator rejects it; review failure catalog.

### Tests for User Story 8

- [ ] T100 [P] [US8] Create grounding validator unit test (injecting fabricated numeric claims and asserting rejection) in `tests/unit/test_grounding_validator.py` (FR-074)
- [ ] T101 [P] [US8] Create prompt log schema and audit trail validation test in `tests/unit/test_promptlog.py`

### Implementation for User Story 8

- [ ] T102 [US8] Implement Groq API provider with Qwen model integration and rate limit / error handling in `src/lpie/llm/groq_provider.py`
- [ ] T103 [US8] Implement strict context grounding validator and hallucination detector in `src/lpie/llm/grounding.py`
- [ ] T104 [US8] Implement reference data dictionary retriever for term definitions in `src/lpie/llm/retriever.py`
- [ ] T105 [US8] Implement curated LLM failure and rejection catalog in `docs/llm-failure-log.md`
- [ ] T106 [US8] Update Narrate stage to generate grounded reviewer case notes with prompt logging in `src/lpie/stages/narrate.py`
- [ ] T107 [US8] Implement Streamlit LLM Copilot interactive reviewer assistant page in `app/pages/7_Copilot.py`

**Checkpoint**: Grounded LLM copilot integrated with Groq Qwen, verified by rejection tests, full audit logging, and interactive UI.

---

## Phase 11: Polish & Cross-Cutting Concerns

**Purpose**: Streamlit Home dashboard, AI development log, end-to-end integration verification, and submission preparation.

- [x] T108 Implement Streamlit Home landing dashboard with executive overview and navigation in `app/Home.py`
- [x] T109 [P] Update AI Development Log with complete session milestones and engineering decisions in `docs/ai-development-log.md`
- [x] T110 [P] Update user documentation and quickstart instructions in `README.md` and `docs/quickstart.md`
- [x] T111 Execute full end-to-end pipeline run across all 14 stages, verify `submission.csv` validity, and record performance metrics in `artifacts/run_manifest.json`
- [x] T112 Run entire pytest test suite (unit, contract, integration) and verify 100% passing tests

---

## Dependencies & Execution Order

### Phase Dependencies

```
Phase 1: Setup
    └── Phase 2: Foundational (BLOCKS all User Stories)
            └── Phase 3: User Story 1 (P1 - Complete Baseline & Submission MVP)
                    ├── Phase 4: User Story 2 (P2 - Data Intelligence & Profiling)
                    │       └── Phase 7: User Story 5 (P3 - Reviewer Queue & Anomalies)
                    ├── Phase 5: User Story 3 (P2 - Multi-Outcome Prediction)
                    │       ├── Phase 6: User Story 4 (P3 - Survival Analysis)
                    │       ├── Phase 8: User Story 6 (P4 - Scenario Projections)
                    │       └── Phase 9: User Story 7 (P4 - Explainability & Error Analysis)
                    └── Phase 10: User Story 8 (P5 - Grounded LLM Copilot)
                            └── Phase 11: Polish & Deliverables
```

### User Story Dependencies

- **US1 (P1)**: Starts immediately after Phase 2 (Foundational). Delivers the MVP submission and runnable pipeline.
- **US2 (P2)**: Builds upon Phase 2 data loaders and US1 Ingest to deliver full profiling and data quality scoring.
- **US3 (P2)**: Builds upon US1 feature pipeline to deliver calibrated GBDTs, baseline comparisons, and reliability diagrams.
- **US4 (P3)**: Depends on US1 label/split structure; implements cause-specific hazard and competing-risks CIF.
- **US5 (P3)**: Depends on US2 validation rules and US1 anomaly scores; builds prioritized reviewer queue.
- **US6 (P4)**: Depends on US3 calibrated models; implements macro scenario shifts and segment aggregations.
- **US7 (P4)**: Depends on US3 trained models; implements TreeSHAP explanations and error analysis.
- **US8 (P5)**: Depends on US1/US5 outputs; implements Groq Qwen copilot with strict grounding controls.

---

## Parallel Execution Opportunities

- **Phase 1 (Setup)**: Tasks T003, T004, T006 can run in parallel.
- **Phase 2 (Foundational)**: Tasks T008, T009, T010, T011, T012, T013, T014 can run in parallel.
- **Phase 3 (US1 Tests)**: Tasks T020, T021, T022, T023, T024, T025, T026 can run in parallel before implementation.
- **Phase 4-10 (Story Tests)**: All contract and unit tests per story (T053-T055, T062-T064, T071-T072, T079-T080, T086-T087, T093-T094, T100-T101) can run in parallel within each phase.
- **Cross-Story Implementation**: Once US1 completes, US2 (Data Profiling) and US3 (Predictive Modeling) can execute in parallel.

---

## Implementation Strategy

### 1. MVP First (User Story 1 - Phase 3)
1. Complete Setup (Phase 1) and Foundational (Phase 2).
2. Write US1 enforcement and contract tests (T020–T026).
3. Implement all 14 pipeline stages with simple, correct implementations.
4. Verify `submission.csv` is generated and passes schema validation.
5. **STOP & VALIDATE**: Run `pytest tests/` and verify the single CLI command runs end-to-end.

### 2. Incremental Value Delivery (Phases 4–10)
- **Increment 1 (Data Intelligence - US2)**: Add deep profiling, drift metrics, and UI page.
- **Increment 2 (Predictive Modeling - US3)**: Add GBDT calibration, baseline comparisons, and reliability curves.
- **Increment 3 (Survival & Competing Risks - US4)**: Add cause-specific hazards and CIF curves.
- **Increment 4 (Reviewer Queue & Anomalies - US5)**: Add prioritized triage queue and reconciliation fixture.
- **Increment 5 (Scenarios & Stress - US6)**: Add macroeconomic scenario simulations.
- **Increment 6 (Explainability - US7)**: Add TreeSHAP attributions and error casebook.
- **Increment 7 (Grounded LLM Copilot - US8)**: Add Groq Qwen integration with grounding validation.

### 3. Final Polish & Video Demo (Phase 11)
- Complete Streamlit UI dashboard across all pages.
- Verify all §11 deliverables and record run manifest metrics.

---

## Phase 12: Convergence

**Purpose**: Execute remaining modular depth components, error analysis, survival models, and Streamlit demonstration surface identified during speckit-converge analysis.

- [x] T113 [P] Implement deep profiling stats, rule evaluators, PSI/KS population drift metrics, and inspectable multi-component quality scoring in `src/lpie/data/profile_stats.py`, `src/lpie/data/rule_evaluator.py`, `src/lpie/data/drift.py`, and `src/lpie/data/quality_score.py` per FR-010, FR-011, FR-013, FR-015, FR-016, FR-017, SC-015, SC-016 (missing)
- [x] T114 [P] Implement unit tests for profiling, validation rules, and drift metrics in `tests/unit/test_profiling_stats.py`, `tests/unit/test_validation_rules.py`, and `tests/unit/test_drift_metrics.py` per spec Testing Requirement (missing)
- [x] T115 [P] Implement right-censored panel dataset builder, cause-specific hazard models, and competing-risks CIF calculator in `src/lpie/survival/dataset.py`, `src/lpie/survival/cause_specific.py`, and `src/lpie/survival/incidence.py` per FR-037, FR-038, FR-039, SC-012 (missing)
- [x] T116 [P] Implement survival CIF bounds and right-censoring unit tests in `tests/unit/test_cif_bounds.py` and `tests/unit/test_survival_hazard.py` per SC-012 (missing)
- [x] T117 [P] Implement prioritized reviewer queue ranking engine (20+ items) and constructed reconciliation fixture in `src/lpie/anomaly/queue.py` and `src/lpie/anomaly/reconciliation.py` per FR-043, FR-046, SC-017, SC-026 (missing)
- [x] T118 [P] Implement false-positive and false-negative error casebook analyzer with driver attribution in `src/lpie/explain/error_analysis.py` and unit test in `tests/unit/test_error_analysis.py` per FR-055, SC-019 (missing)
- [x] T119 [P] Implement live Groq Qwen provider, field dictionary retriever, and curated rejection failure catalog in `src/lpie/llm/groq_provider.py`, `src/lpie/llm/retriever.py`, and `docs/llm-failure-log.md` per FR-057, FR-062, SC-022 (missing)
- [x] T120 Implement multi-page Streamlit demo dashboard reading artifacts in `app/Home.py` and `app/pages/1_Data_Intelligence.py` through `7_Copilot.py` per FR-068 (missing)


