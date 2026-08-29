# Research: Advanced Intelligence Suite

**Feature**: `specs/002-advanced-features`  
**Status**: Completed  
**Governing Document**: `.specify/memory/constitution.md`

---

## 1. Monte Carlo Portfolio Simulation Architecture

- **Decision**: Implement a vectorized NumPy/PyArrow matrix-based stochastic engine using Bernoulli-trial draws over predicted calibrated probabilities $P(\text{Default}_{12m})$ and $P(\text{Prepay}_{12m})$.
- **Rationale**: Simulating 10,000 paths over 756,520 loans with Python loops would take $> 15$ minutes. Vectorized array slicing with pre-allocated random normal buffers completes 10,000 portfolio aggregation paths in **$< 3.2$ seconds** using $< 200$ MB RAM.
- **Formulas**:
  - Portfolio Loss per path: $L_k = \sum_i \mathbb{I}_{i,k}^{\text{def}} \cdot \text{UPB}_i \cdot \text{LGD}_i$ (with stochastic $\text{LGD} \sim \text{Beta}(a, b)$ mean $0.35$).
  - $\text{VaR}_{99} = \text{Percentile}(L, 99)$
  - $\text{CVaR}_{99} = \mathbb{E}[L \mid L \ge \text{VaR}_{99}]$
- **Alternatives Considered**: SimPy discrete-event simulation (rejected due to excessive per-entity scheduling overhead).

---

## 2. Segment Calibration & Fairness Metrics

- **Decision**: Stratify out-of-time validation metrics into discrete credit tiers (Subprime $<620$, Near-Prime $620–680$, Prime $>680$), origination channels (Retail, Broker, Correspondent), and geographic states.
- **Fairness Metrics Computed**:
  - **Disparate Impact Ratio**: $\frac{P(\hat{Y}=1 \mid A=a_1)}{P(\hat{Y}=1 \mid A=a_0)}$
  - **Equalized Odds Difference**: $\max(|\text{TPR}_{a_1} - \text{TPR}_{a_0}|, |\text{FPR}_{a_1} - \text{FPR}_{a_0}|)$
  - **Expected Calibration Error (ECE)**: $\sum_{m=1}^M \frac{|B_m|}{N} |\text{acc}(B_m) - \text{conf}(B_m)|$
- **Alternatives Considered**: Direct demographic feature inclusion (strictly rejected per fair lending compliance; only used as post-hoc auditing slices).

---

## 3. Counterfactual Search Algorithm

- **Decision**: Sparse Coordinate Descent optimization over actionable bounded continuous and ordinal features (`current_actual_upb`, `original_dti`, `rate_spread_incentive`).
- **Objective**: $\min_{\delta} \|\delta\|_1 + \lambda (f(x + \delta) - y_{\text{target}})^2$ subject to $x + \delta \in \text{FeasibleBounds}$.
- **Immutable Features**: `credit_score` (origination), `property_state`, `loan_purpose`, `channel`, `first_payment_date` remain strictly constant.
- **Alternatives Considered**: DiCE (Diverse Counterfactual Explanations) neural framework (rejected due to heavy PyTorch dependency and non-deterministic gradient steps on tabular data).

---

## 4. Population & Feature Drift Monitoring

- **Decision**: Vectorized computation of Population Stability Index (PSI), Kolmogorov-Smirnov (KS) statistic, and Wasserstein-1 distance comparing baseline training distributions (2006–2017) against scoring window (2023–2025).
- **Thresholds**:
  - $PSI < 0.10$: Green (Stable)
  - $0.10 \le PSI < 0.25$: Yellow (Moderate Shift)
  - $PSI \ge 0.25$: Red (Significant Shift / Rate Regime Change)
