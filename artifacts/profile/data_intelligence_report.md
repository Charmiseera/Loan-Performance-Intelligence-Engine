# Data Intelligence and Profiling Report

- **Total Loans Ingested**: 60,000
- **Total Monthly Performance Records**: 3,854,595
- **Batch Quality Score**: 100.0 / 100.0 (High Quality Share: 100.0%)
- **Completeness / Validity / Consistency**: 40.0 / 30.0 / 30.0

## Deterministic Cross-Column Rule Evaluations
- **Interest Rate Reasonable Range (0-30%)**: 0 violations (0.00%) — Severity: HIGH

## Population Drift Analysis (Top Shifted Features)
| Feature | PSI | KS Statistic | Drift Status |
|---|---|---|---|
| monthly_reporting_period | 8.2818 | 1.0000 | SIGNIFICANT_DRIFT |
| misc_expenses | 2.2326 | 0.3790 | SIGNIFICANT_DRIFT |
| current_interest_rate | 2.0986 | 0.5169 | SIGNIFICANT_DRIFT |
| current_month_modification_cost | 1.5386 | 0.5036 | SIGNIFICANT_DRIFT |
| modification_cost | 1.5099 | 0.5235 | SIGNIFICANT_DRIFT |