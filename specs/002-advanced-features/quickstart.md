# Quickstart & Validation Guide: Advanced Intelligence Suite

**Feature**: `specs/002-advanced-features`  
**Status**: Ready

---

## 1. Execution Commands

To execute the entire advanced intelligence suite end-to-end:

```bash
# Run pipeline with advanced scenario & fairness modeling
python -m lpie run --config config/pipeline.yaml

# Run all automated unit and contract tests
python -m pytest tests/ -q
```

---

## 2. Interactive Streamlit Validation

1. Launch dashboard:
   ```bash
   streamlit run app/Home.py
   ```
2. Navigate to:
   - **`5_Scenarios`**: View portfolio Monte Carlo distribution percentiles ($p_{10}, p_{50}, p_{90}, p_{99}$, VaR, Expected Shortfall).
   - **`6_Explainability`**: View counterfactual "what-if" guidance for high-risk loans.
   - **`1_Data_Intelligence`**: View high-resolution multi-feature PSI drift tables.
   - **`7_Copilot`**: View live Groq Qwen case notes incorporating counterfactual recommendations and grounding checks.

---

## 3. Automated Contract Tests

- `test_monte_carlo_bounds.py`: Asserts $0 \le \text{VaR}_{95} \le \text{VaR}_{99} \le \text{TotalUPB}$.
- `test_fairness_audit_schema.py`: Verifies Disparate Impact Ratio and ECE computations across segments.
- `test_counterfactual_bounds.py`: Verifies immutable features remain unaltered during counterfactual search.
