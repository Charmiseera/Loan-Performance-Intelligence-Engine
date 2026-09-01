# Model Card: Loan Performance Intelligence Engine (LPIE)

**Date**: 2026-08-28
**Version**: 1.0.0
**Model Type**: Calibrated LightGBM Gradient Boosted Decision Trees & Multinomial State Classifiers
**Evaluation Window**: Out-of-time scoring panel (202301–202512)

---

## 1. Intended Use & Model Summary

LPIE provides loan-level multi-horizon risk scoring, deterioration prediction, prepayment modeling, anomaly triage, and grounded review assistance for residential mortgage portfolios.

### Key Outputs
- **3-Month / 6-Month Deterioration Probability** (`prob_deterioration_3m`, `prob_deterioration_6m`): Likelihood of delinquency bucket escalation.
- **12-Month Default Probability** (`prob_default_12m`): Likelihood of credit event termination (Third party sale, short sale, REO, note sale) or 90+ DPD.
- **12-Month Prepayment Probability** (`prob_prepay_12m`): Likelihood of voluntary payoff.
- **Next State** (`next_state`): Categorical forecast of loan delinquency status in the subsequent month.
- **Anomaly Score & Action** (`anomaly_score`, `recommended_action`): Hybrid rule-statistical exception detection.

---

## 2. Performance Metrics (Out-of-Time Test Split)

| Outcome Target | Positive Base Rate | PR-AUC (Average Precision) | ROC-AUC | Brier Score |
|---|---|---|---|---|
| 3-Month Deterioration | 0.0315 | 0.6087 | 0.8972 | 0.0169 |
| 6-Month Deterioration | 0.0429 | 0.5366 | 0.858 | 0.0261 |
| 12-Month Default | 0.0266 | 0.6199 | 0.9023 | 0.0136 |
| 12-Month Prepayment | 0.1793 | 0.3195 | 0.6648 | 0.137 |

---

## 3. Leakage Containment & Governance

- **Temporal Disjointness**: Training (2006–2017), Validation (2019–2021), and Scoring (2023–2025) windows maintain a mandatory 12-month embargo gap.
- **As-Of Enforcement**: Feature builders declare explicit retrospective windows; forward-looking windows are statically rejected.
- **Grounded LLM Rule (Principle I)**: All model predictions and actions in `submission.csv` are produced strictly by quantitative models without LLM generation.