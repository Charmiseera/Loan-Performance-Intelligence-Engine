# Data Model: Advanced Intelligence Suite

**Feature**: `specs/002-advanced-features`  
**Status**: Ready

---

## 1. Entities & Schema Definitions

### A. `MonteCarloSimulationResult` (`artifacts/scenario/monte_carlo_results.json`)
```json
{
  "num_iterations": 10000,
  "total_active_loans": 756520,
  "total_active_upb": 172165280000.0,
  "portfolio_expected_loss": 1542890200.0,
  "expected_loss_rate": 0.00896,
  "var_95": 2189400000.0,
  "var_99": 2845600000.0,
  "cvar_99": 3125000000.0,
  "prepayment_cashflow_std": 485000000.0,
  "loss_distribution_percentiles": {
    "p10": 980000000.0,
    "p50": 1520000000.0,
    "p90": 2040000000.0,
    "p95": 2189400000.0,
    "p99": 2845600000.0
  }
}
```

### B. `SubgroupFairnessAudit` (`artifacts/reports/fairness_audit_report.json`)
```json
{
  "audit_timestamp": "2026-08-28T23:50:00Z",
  "credit_tier_parity": {
    "Subprime (<620)": {"sample_count": 48200, "brier_score": 0.0482, "ece": 0.0018, "fpr": 0.124},
    "Near-Prime (620-680)": {"sample_count": 182400, "brier_score": 0.0241, "ece": 0.0009, "fpr": 0.065},
    "Prime (>680)": {"sample_count": 390492, "brier_score": 0.0078, "ece": 0.0004, "fpr": 0.018}
  },
  "channel_fairness": {
    "Retail": {"disparate_impact_ratio": 1.00, "equalized_odds_diff": 0.00},
    "Broker": {"disparate_impact_ratio": 0.98, "equalized_odds_diff": 0.01},
    "Correspondent": {"disparate_impact_ratio": 1.01, "equalized_odds_diff": 0.01}
  }
}
```

### C. `CounterfactualRecommendation` (Internal schema for Reviewer Copilot / Explainability)
```json
{
  "loan_id": "F20Q30069712",
  "baseline_default_prob": 0.184,
  "target_default_prob": 0.040,
  "actionable_perturbations": {
    "current_actual_upb": {"current": 285000.0, "recommended": 210000.0, "delta": -75000.0},
    "rate_spread_incentive": {"current": 1.25, "recommended": -0.50, "delta": -1.75}
  },
  "feasibility_score": 0.88,
  "immutable_features_preserved": true
}
```
