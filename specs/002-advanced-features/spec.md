# Feature Specification: Advanced Intelligence Suite

**Feature Directory**: `specs/002-advanced-features`  
**Created**: 2026-08-28  
**Status**: Ready for Review / Planning  
**Input**: Intain Campus FinTech Challenge 2026 — Section 10 Advanced Features Specification:
- Competing-risk survival modeling
- Monte Carlo portfolio loss & prepayment simulation
- Population & feature drift monitoring dashboard
- Segment-level scenario stress curves
- Model calibration by vintage and credit band
- RAG over official data dictionary and validation rules
- Bias & fairness parity analysis (geography, channel, unit count)
- Counterfactual explanation generation
- Model prediction confidence intervals & uncertainty quantification
- Human-in-the-loop active learning queue & synthetic stress fixture

**Governing document**: [`.specify/memory/constitution.md`](../../.specify/memory/constitution.md) (Principles I–VI strictly enforced).

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Portfolio Monte Carlo Loss & Prepayment Simulation (Priority: P1)
**Stakeholder Goal**: Portfolio Risk Manager & Quantitative Analyst  
As a portfolio risk manager, I need to run a 10,000-path stochastic Monte Carlo simulation on the active mortgage pool across multiple macro rate and unemployment scenarios, so that I can estimate Value-at-Risk (VaR 99%), Expected Shortfall (CVaR), and prepayment cash-flow volatility.

**Acceptance Scenarios**:
1. **Given** 756,520 scored loans and calibrated default/prepayment probabilities, **When** the user triggers a 10,000-iteration Monte Carlo simulation, **Then** the engine outputs the portfolio loss distribution, 95% and 99% Value-at-Risk, Expected Shortfall, and prepayment standard deviation within 5 seconds.
2. **Given** an adverse rate spike or recession scenario, **When** simulated, **Then** cash flows shift dynamically and cumulative loss percentiles are plotted as an empirical CDF.

---

### User Story 2 - Subgroup Calibration & Fairness Parity Audit (Priority: P1)
**Stakeholder Goal**: Model Risk Management (MRM) & Compliance Officer  
As a compliance and model validation officer, I need to evaluate calibration curves (Brier score, ECE) stratified by loan vintage, credit tier (Subprime <620, Near-prime 620–680, Prime >680), property state, and origination channel, so that I can confirm equitable predictive performance across borrower segments without disparate impact.

**Acceptance Scenarios**:
1. **Given** out-of-time validation predictions, **When** stratified calibration analysis runs, **Then** Expected Calibration Error (ECE) is reported per credit score tier and vintage.
2. **Given** demographic proxies (e.g. Geography, First-time Homebuyer flag), **When** fairness parity is evaluated, **Then** demographic parity ratios, equalized odds differences, and disparate impact metrics are generated.

---

### User Story 3 - Counterfactual Explanations & What-If Credit Sensitivity (Priority: P2)
**Stakeholder Goal**: Loan Reviewer & Underwriting Specialist  
As a mortgage credit reviewer, I need counterfactual "what-if" guidance for flagged or high-risk loans (e.g., "What minimum UPB paydown or credit score improvement would reduce 12-month default risk below 2.0%?"), so that I can understand actionable risk mitigants.

**Acceptance Scenarios**:
1. **Given** an individual loan with high predicted default probability ($p > 0.15$), **When** counterfactual analysis is requested, **Then** the engine computes the closest sparse perturbation in actionable feature space (UPB, rate, DTI) that lowers $p$ below target.
2. **Given** non-actionable immutable features (e.g. `first_payment_date`), **When** counterfactuals are generated, **Then** immutable features remain strictly frozen.

---

### User Story 4 - High-Resolution Drift Monitoring & Alerting Dashboard (Priority: P2)
**Stakeholder Goal**: Production ML Ops & Data Quality Auditor  
As a data engineer and ML ops auditor, I need continuous tracking of Population Stability Index (PSI), Wasserstein Distance, and Kolmogorov-Smirnov (KS) statistics across all 35 panel features and 31 origination fields, with automated visual alerts when drift exceeds threshold ($PSI > 0.10$).

**Acceptance Scenarios**:
1. **Given** feature matrices from historical baseline vs scoring window, **When** drift monitor runs, **Then** features are categorized as Green ($PSI < 0.10$), Yellow ($0.10 \le PSI < 0.25$), or Red ($PSI \ge 0.25$).
2. **Given** red drift features (e.g. `original_interest_rate`), **When** viewed in the dashboard, **Then** empirical histogram overlays explain the underlying macroeconomic shift.

---

### User Story 5 - Epistemic & Aleatoric Uncertainty Quantification (Priority: P3)
**Stakeholder Goal**: Institutional Underwriting & Capital Planning  
As a capital allocation officer, I need prediction confidence intervals for every scored loan-month (combining GBDT tree variance and calibrated isotonic intervals), so that capital buffers account for model uncertainty.

**Acceptance Scenarios**:
1. **Given** test loan features, **When** inference runs, **Then** the model outputs point estimate, 5th percentile lower bound, 95th percentile upper bound, and an uncertainty tier (`LOW`, `MEDIUM`, `HIGH`).

---

## Functional Requirements

- **FR-101**: The system MUST implement a vectorized Monte Carlo simulation engine executing $\ge 1,000$ stochastic iterations over the 756,520 portfolio records in $< 5$ seconds.
- **FR-102**: The simulation MUST report Portfolio Expected Loss, 95% VaR, 99% VaR, 99% Expected Shortfall (CVaR), and total cash-flow prepayment standard deviation.
- **FR-103**: The calibration engine MUST evaluate Brier Score and Expected Calibration Error (ECE) across at least 3 credit tiers (Subprime, Near-Prime, Prime) and 6 vintages.
- **FR-104**: The bias and fairness analyzer MUST compute Demographic Parity Ratio, False Positive Rate Parity, and Disparate Impact Ratio across `property_state`, `channel`, and `occupancy_status`.
- **FR-105**: The counterfactual generator MUST optimize sparse feature modifications constrained to actionable variables (`current_actual_upb`, `original_dti`, `rate_spread_incentive`), preserving immutable origination characteristics.
- **FR-106**: The drift monitoring module MUST compute PSI, KS statistic, and Wasserstein distance for all numeric and categorical features, outputting a machine-readable `advanced_drift_metrics.json`.
- **FR-107**: The uncertainty engine MUST compute 90% confidence intervals ($[p_{05}, p_{95}]$) for all 4 prediction horizons using GBDT leaf path ensemble variance.
- **FR-108**: All advanced features MUST be interactive in the Streamlit UI under dedicated dashboard tabs.
- **FR-109**: All advanced outputs MUST remain strictly non-LLM and deterministic, adhering to **Principle I** and **Principle II**.

---

## Success Criteria

1. **Simulation Performance**: 10,000-path portfolio Monte Carlo simulation completes in $< 5.0$ seconds without out-of-memory errors.
2. **Fairness Audit Coverage**: 100% of validation records analyzed across credit tiers and demographic proxies with full metric exports.
3. **Counterfactual Feasibility**: Counterfactual generation returns a valid, sparse perturbation for $> 95\%$ of target test loans.
4. **Uncertainty Bounds**: 90% empirical coverage on out-of-time validation data matches nominal calibration target within $\pm 3\%$.
5. **Zero Disqualification Risk**: 0% LLM dependency for numeric computations; 100% test pass rate across automated regression tests.

---

## Key Entities & Data Contracts

- `monte_carlo_results.json`: Schema containing `{num_iterations, var_95, var_99, cvar_99, expected_loss, prepayment_volatility, loss_percentiles}`.
- `fairness_audit_report.json`: Schema containing `{subgroup_metrics, disparate_impact_ratios, equalized_odds_differences}`.
- `calibration_by_segment.json`: Schema containing `{vintage_ece, credit_tier_brier, channel_calibration}`.
- `advanced_drift_summary.parquet`: Dataframe with columns `[feature_name, psi, ks_stat, wasserstein_dist, drift_tier, alert_level]`.
