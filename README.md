# Loan Performance Intelligence Engine (LPIE)

> **Intain Campus FinTech Challenge 2026 — AI Track Submission**

[![Tests](https://img.shields.io/badge/tests-50%20passing-brightgreen)]()
[![Pipeline](https://img.shields.io/badge/pipeline-14%20stages-blue)]()
[![Submission](https://img.shields.io/badge/submission.csv-756%2C520%20rows-green)]()
[![ROC-AUC](https://img.shields.io/badge/ROC--AUC%20(12m%20default)-0.9023-success)]()

---

## 🗺️ Deliverables Navigator

This table maps every **Required Deliverable** from the challenge specification to its exact location in this repository:

| Deliverable | Description | File Location in Repository |
|---|---|---|
| **1. GitHub Repository** | Complete, clean source code | `https://github.com/Charmiseera/Loan-Performance-Intelligence-Engine` |
| **2. Reproducible Pipeline** | End-to-end ML pipeline CLI | [`src/lpie/`](file:///d:/Intain/src/lpie/) (Run: `python -m lpie run`) |
| **3. Final `submission.csv`** | 756,520 scored records (13 cols) | [`artifacts/submission/submission.csv`](file:///d:/Intain/artifacts/submission/submission.csv) |
| **4. Model Card** | Governance, features, limitations | [`artifacts/reports/model_card.md`](file:///d:/Intain/artifacts/reports/model_card.md) |
| **5. Data Intelligence Report** | Quality scores, drift, missingness | [`artifacts/profile/data_intelligence_report.md`](file:///d:/Intain/artifacts/profile/data_intelligence_report.md) |
| **6. Explainability Report** | TreeSHAP, counterfactuals, error cases | [`artifacts/explain/explainability_report.md`](file:///d:/Intain/artifacts/explain/explainability_report.md) |
| **7. Scenario Stress Report** | Base, Adverse, High Prepayment + MC | [`artifacts/scenario/scenario_report.md`](file:///d:/Intain/artifacts/scenario/scenario_report.md) |
| **8. Grounded LLM Copilot** | Interactive anti-hallucination assistant | Page 7 in Dashboard (`app/pages/7_Copilot.py`) |
| **9. AI Development Log** | Immutable prompt & dev audit log | [`docs/ai-development-log.md`](file:///d:/Intain/docs/ai-development-log.md) |
| **10. Interactive Dashboard** | 8-Page Streamlit FinTech Portal | [`app/Home.py`](file:///d:/Intain/app/Home.py) (Run: `streamlit run app/Home.py`) |

---

## 🏆 100-Point Judging Criteria Mapping

| Criterion | Pts | What Judges Look For | Implementation & Verification Location |
|---|:---:|---|---|
| **Data Intelligence & Profiling** | 15 | Missingness, outliers, train/test drift, data quality score | Page 1 (`1_Data_Intelligence.py`), [`artifacts/profile/data_intelligence_report.md`](file:///d:/Intain/artifacts/profile/data_intelligence_report.md) |
| **Predictive Modeling** | 20 | GBDT models, time-aware split, default/delinquency/prepayment, calibration | Page 2 (`2_Predictions.py`), [`src/lpie/models/gbdt.py`](file:///d:/Intain/src/lpie/models/gbdt.py), [`artifacts/train/model_comparison.json`](file:///d:/Intain/artifacts/train/model_comparison.json) |
| **Time-to-Event Modeling** | 15 | Competing-risk survival, Aalen-Johansen CIF curves | Page 3 (`3_Time_To_Event.py`), [`src/lpie/models/survival.py`](file:///d:/Intain/src/lpie/models/survival.py), [`artifacts/survival/survival_curves.json`](file:///d:/Intain/artifacts/survival/survival_curves.json) |
| **Anomaly Intelligence** | 10 | Suspicious records, IsolationForest + rule severity, reviewer queue | Page 4 (`4_Reviewer_Queue.py`), [`src/lpie/stages/anomaly.py`](file:///d:/Intain/src/lpie/stages/anomaly.py), [`artifacts/anomaly/reviewer_queue.json`](file:///d:/Intain/artifacts/anomaly/reviewer_queue.json) |
| **Scenario Stress Simulation** | 10 | Base/Adverse/High-Prepay, Monte Carlo loss distribution, VaR/CVaR | Page 5 (`5_Scenarios.py`), [`src/lpie/advanced/monte_carlo.py`](file:///d:/Intain/src/lpie/advanced/monte_carlo.py), [`artifacts/scenario/monte_carlo_results.json`](file:///d:/Intain/artifacts/scenario/monte_carlo_results.json) |
| **Explainability & Fair Lending** | 10 | TreeSHAP global/local, counterfactuals, error casebook, fair lending parity | Page 6 (`6_Explainability.py`), [`src/lpie/explain/counterfactual.py`](file:///d:/Intain/src/lpie/explain/counterfactual.py), [`artifacts/reports/fairness_audit_report.json`](file:///d:/Intain/artifacts/reports/fairness_audit_report.json) |
| **Smart LLM Usage** | 10 | Grounded LLM, reviewer summaries, anti-hallucination validator | Page 7 (`7_Copilot.py`), [`src/lpie/llm/grounding.py`](file:///d:/Intain/src/lpie/llm/grounding.py), [`artifacts/narrate/prompt_log.jsonl`](file:///d:/Intain/artifacts/narrate/prompt_log.jsonl) |
| **ML Engineering & Clean Code** | 5 | Modular CLI, 50/50 passing tests, clean architecture | [`src/lpie/cli.py`](file:///d:/Intain/src/lpie/cli.py), [`tests/`](file:///d:/Intain/tests/), [`pyproject.toml`](file:///d:/Intain/pyproject.toml) |
| **Agentic Coding Evidence** | 5 | AI Development Log, prompt log, rejected AI output test cases | [`docs/ai-development-log.md`](file:///d:/Intain/docs/ai-development-log.md), Page 7 Step 13 Rejection Audit button |

---

## 🎬 15-Point Demo Video Navigator

If reviewing or recording the 5-minute video flow, here is where each of the 15 required points lives in the application:

1. **Dataset & Targets**: `Home.py` Executive Tiles & `artifacts/submission/submission_manifest.json`
2. **Data Profiling Report**: Page 1 (`1_Data_Intelligence.py`) Section 1 & 2 (Score: 86.4/100)
3. **Top Data Quality Issues**: Page 1 Section 3 (Missingness: VantageScore 4 100%, Program Indicator 98.6%) & Section 5 (4,431 Violations)
4. **Feature Engineering Approach**: Page 2 (`2_Predictions.py`) Section 2 (Rate Spread Incentive, Paydown Velocities 3m/6m, UPB Acceleration, DTI x LTV Product)
5. **Time-Aware Split**: Page 2 Section 1 (Train 2006-2017 [1.95M], Val 2019-2021 [621K], Scoring 2023-2025 [756K], 12m Embargo)
6. **Baseline Model Performance**: Page 2 Section 3 (Logistic Regression Baseline: Default AUC 0.8832)
7. **Improved Model Performance**: Page 2 Section 3 (LightGBM Improved: Default AUC 0.9023, Delinquency 0.8972, Prepayment 0.6648)
8. **Survival / Transition Model Output**: Page 3 (`3_Time_To_Event.py`) Aalen-Johansen CIF curves (Sum <= 1.0 Passed)
9. **Anomaly Examples**: Page 4 (`4_Reviewer_Queue.py`) Operational Triage Queue (Loan `F21Q40848300` Rank #1)
10. **Scenario Output**: Page 5 (`5_Scenarios.py`) Section 1 (Stress Scenarios) & Section 2 (Monte Carlo Expected Loss $835M, VaR 99 $1.30B, CVaR 99 $1.44B)
11. **Local Explanation for One Loan**: Page 6 (`6_Explainability.py`) Tab 2 (Local TreeSHAP Waterfall for Loan `F21Q40848300`) & Sparse Counterfactual Calculator
12. **LLM Reviewer Note**: Page 7 (`7_Copilot.py`) Section 2 (Live Groq Qwen Note Generation)
13. **Rejected LLM Output Example**: Page 7 Section 2 (Step 13 `Run Hallucination Rejection Audit` button showing red REJECTED warning)
14. **Final Submission File**: `Home.py` Section 4 (`artifacts/submission/submission.csv` - 756,520 rows, 13 cols, PASSED)
15. **AI Development Log**: `Home.py` Section 5 & [`docs/ai-development-log.md`](file:///d:/Intain/docs/ai-development-log.md)

---

## 🏛️ Core Principles

> Enforced by automated test gates (`pytest tests/`).

* **Principle I — ML-First (The LLM Never Decides)**: All predictions, probability curves, and queue prioritization originate from calibrated ML/GBDT models. The LLM produces reviewer recommendations only, governed by Grounding Validation.
* **Principle II — Strict Leakage Containment**: Temporal embargos and forward-window label definitions eliminate lookahead bias across train/validation/scoring splits (`tests/unit/test_leakage_guard.py`).
* **Principle III — Grounded LLM Governance**: Rejection validation intercepts and blocks any ungrounded numerical claims before presentation (`src/lpie/llm/grounding.py`).
* **Principle IV — Contract Integrity & Reproducibility**: All scoring outputs conform to exact contract schemas, derived from a single root seed (`root_seed: 42`).

---

## ⚡ Quick Start

### 1. Requirements & Setup

```bash
# Python 3.11+ required
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Mac / Linux

pip install -e ".[dev]"
```

### 2. Run the Full ML Pipeline

```bash
python -m lpie run --config config/pipeline.yaml
```

This single command executes all 14 pipeline stages end-to-end and populates all artifact files.

### 3. Validate Submission Contract

```bash
python -m lpie validate --submission artifacts/submission/submission.csv
```

### 4. Run Automated Test Suite (50 Tests)

```bash
python -m pytest tests/ -q
# Expected: 50 passed
```

### 5. Launch Interactive Reviewer Dashboard

```bash
streamlit run app/Home.py --server.port 8501
```

Open **`http://localhost:8501`** in your browser.

---

## 🐳 Docker Deployment

```bash
# Build production Docker container
docker build -t lpie-app .

# Run container
docker run -p 8501:8501 -e GROQ_API_KEY="your_groq_key" lpie-app
```
