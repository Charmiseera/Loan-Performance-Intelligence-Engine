# Portfolio Scenario and Stress Simulation Report

> **Note**: All scenario inputs are stated assumptions, not economic forecasts.

## Portfolio-Level Projections

| Scenario | Default Rate | Prepayment Rate | Deterioration Rate |
|---|---|---|---|
| Baseline | 1.49% | 12.34% | 2.86% |
| Adverse | 4.18% | 4.93% | 6.29% |
| High Prepayment | 1.20% | 30.84% | 2.57% |

## Monte Carlo Stochastic Portfolio Loss Simulation

- **Simulated Paths**: 1,000
- **Portfolio Expected Loss**: $835,306,501.65 (0.51%)
- **95% Value-at-Risk (VaR 95)**: $1,159,563,014.79
- **99% Value-at-Risk (VaR 99)**: $1,300,289,092.22
- **99% Expected Shortfall (CVaR 99)**: $1,440,278,396.10
- **Prepayment Cashflow StdDev**: $68,975,943.88

## Top Drivers of Deviation from Baseline (12m Default Rate)

### Baseline
- **property_state=PR**: 8.07% (+6.58% vs portfolio avg) — 1,153 loan-months
- **channel=T**: 7.46% (+5.97% vs portfolio avg) — 11,195 loan-months
- **original_loan_term=258**: 4.39% (+2.90% vs portfolio avg) — 36 loan-months
- **original_loan_term=264**: 3.91% (+2.41% vs portfolio avg) — 284 loan-months
- **servicer_name=NEWREZ LLC**: 3.55% (+2.06% vs portfolio avg) — 664 loan-months

### Adverse
- **property_state=PR**: 22.59% (+18.41% vs portfolio avg) — 1,153 loan-months
- **channel=T**: 20.89% (+16.71% vs portfolio avg) — 11,195 loan-months
- **original_loan_term=258**: 12.29% (+8.11% vs portfolio avg) — 36 loan-months
- **original_loan_term=264**: 10.94% (+6.75% vs portfolio avg) — 284 loan-months
- **servicer_name=NEWREZ LLC**: 9.94% (+5.76% vs portfolio avg) — 664 loan-months

### High Prepayment
- **property_state=PR**: 6.46% (+5.26% vs portfolio avg) — 1,153 loan-months
- **channel=T**: 5.97% (+4.78% vs portfolio avg) — 11,195 loan-months
- **original_loan_term=258**: 3.51% (+2.32% vs portfolio avg) — 36 loan-months
- **original_loan_term=264**: 3.12% (+1.93% vs portfolio avg) — 284 loan-months
- **servicer_name=NEWREZ LLC**: 2.84% (+1.65% vs portfolio avg) — 664 loan-months
