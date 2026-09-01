# Loan Performance Intelligence Engine (LPIE)

> **Intain Campus FinTech Challenge 2026 — AI Track Submission**

[![Tests](https://img.shields.io/badge/tests-50%20passing-brightgreen)]()
[![Pipeline](https://img.shields.io/badge/pipeline-14%20stages-blue)]()
[![Submission](https://img.shields.io/badge/submission.csv-756%2C520%20rows-green)]()
[![ROC-AUC](https://img.shields.io/badge/ROC--AUC%20(12m%20default)-0.9023-success)]()

---

## 🗺️ System Architecture & Deliverables Navigator

| Component / Deliverable | Description | Location in Repository |
|---|---|---|
| **1. Source Repository** | Complete modular Python source code | [`src/lpie/`](file:///d:/Intain/src/lpie/) |
| **2. Pipeline CLI Engine** | End-to-end ML pipeline runner | [`src/lpie/cli.py`](file:///d:/Intain/src/lpie/cli.py) (`python -m lpie run`) |
| **3. Final `submission.csv`** | 756,520 scored records (13 contract cols) | [`artifacts/submission/submission.csv`](file:///d:/Intain/artifacts/submission/submission.csv) |
| **4. Model Card** | Governance, features, metrics, limitations | [`artifacts/reports/model_card.md`](file:///d:/Intain/artifacts/reports/model_card.md) |
| **5. Data Intelligence Report** | Quality scores, drift, missingness audit | [`artifacts/profile/data_intelligence_report.md`](file:///d:/Intain/artifacts/profile/data_intelligence_report.md) |
| **6. Explainability Report** | TreeSHAP, counterfactuals, FP/FN error cases | [`artifacts/explain/explainability_report.md`](file:///d:/Intain/artifacts/explain/explainability_report.md) |
| **7. Scenario Stress Report** | Base, Adverse, High Prepayment + Monte Carlo | [`artifacts/scenario/scenario_report.md`](file:///d:/Intain/artifacts/scenario/scenario_report.md) |
| **8. Grounded LLM Copilot** | Interactive anti-hallucination assistant | [`app/pages/7_Copilot.py`](file:///d:/Intain/app/pages/7_Copilot.py) |
| **9. AI Development Log** | Immutable prompt & development audit log | [`docs/ai-development-log.md`](file:///d:/Intain/docs/ai-development-log.md) |
| **10. Reviewer Dashboard** | 8-Page Streamlit Institutional Web App | [`app/Home.py`](file:///d:/Intain/app/Home.py) (`streamlit run app/Home.py`) |

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
