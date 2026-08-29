# Loan Performance Intelligence Engine (LPIE)

> **Intain Campus FinTech Challenge 2026 — AI Track**

[![Tests](https://img.shields.io/badge/tests-34%20passing-brightgreen)]()
[![Pipeline](https://img.shields.io/badge/pipeline-14%20stages-blue)]()
[![Submission](https://img.shields.io/badge/submission.csv-756%2C520%20rows-green)]()
[![ROC-AUC](https://img.shields.io/badge/ROC--AUC%20(12m%20default)-0.901-success)]()

---

## Principles

> These principles are **non-negotiable** and enforced by automated test rather than convention.

**Principle I — ML-First: The LLM Never Decides**
Every value in `submission.csv` originates from a trained ML model. No predicted value is produced by generated text. The LLM produces reviewer *recommendations* only, and those are labelled as such.

**Principle II — Leakage Containment**
No outcome column and no outcome-derived column may reach a fitted model's feature matrix. Enforced by `tests/unit/test_leakage_guard.py`.

**Principle III — Grounded LLM Governance**
LLM output is validated against its grounding context before surfacing to reviewers. Fabricated or unsupported numeric claims are rejected and logged. Prompt log is append-only.

**Principle IV — Reproducibility by Construction**
All randomness derives from a single configured seed. Two runs with identical configuration produce byte-identical `submission.csv`. Enforced by `tests/integration/test_determinism.py`.

**Principle V — Honest Reporting & Declared Limits**
Every number in every report is traceable to a machine-readable artifact produced by the same run. No threshold is fabricated, no metric is cherry-picked.

---

## Quick Start

### Requirements

- Python 3.11+
- ~4 GB RAM (2 GB for ingest, 1.5 GB for train)
- Freddie Mac R47 sample files in `data/raw/`

### Install

```bash
python -m venv .venv
.venv\Scripts\activate           # Windows
pip install -e .
```

### Run the Full Pipeline

```bash
python -m lpie run --config config/pipeline.yaml
```

This single command runs all 14 stages end-to-end and produces every deliverable:

| Artifact | Location |
|----------|----------|
| `submission.csv` | `artifacts/submission/submission.csv` |
| Model card | `artifacts/reports/model_card.md` |
| Data intelligence report | `artifacts/reports/data_intelligence_report.md` |
| Explainability report | `artifacts/reports/explainability_report.md` |
| Scenario report | `artifacts/reports/scenario_report.md` |
| Reviewer notes | `artifacts/narrate/reviewer_notes.md` |
| Prompt log | `artifacts/narrate/prompt_log.jsonl` |
| Run manifest | `artifacts/run_manifest.json` |

### Run a Single Stage

```bash
python -m lpie stage <stage_name> --config config/pipeline.yaml
# e.g.: python -m lpie stage profile
```

### Validate Submission

```bash
python -m lpie validate --submission artifacts/submission/submission.csv
```

### Run Tests

```bash
python -m pytest tests/ -q
# Expected: 34 passed
```

---

## Pipeline Architecture

```
data/raw/                     (Freddie Mac R47 pipe-delimited files)
    │
    ▼
┌─────────┐  ┌──────────┐  ┌───────┐  ┌─────────┐  ┌───────┐  ┌──────────┐
│  ingest │→ │ contract │→ │ label │→ │ profile │→ │ split │→ │ survival │
└─────────┘  └──────────┘  └───────┘  └─────────┘  └───────┘  └──────────┘
                                                                     │
    ┌────────────────────────────────────────────────────────────────┘
    ▼
┌──────────┐  ┌───────┐  ┌─────────┐  ┌─────────┐  ┌──────────┐
│ features │→ │ train │→ │ explain │→ │ anomaly │→ │ scenario │
└──────────┘  └───────┘  └─────────┘  └─────────┘  └──────────┘
                                                         │
    ┌────────────────────────────────────────────────────┘
    ▼
┌─────────┐  ┌────────┐  ┌────────┐
│ narrate │→ │ report │→ │ submit │
└─────────┘  └────────┘  └────────┘
                              │
                              ▼
                    artifacts/submission/submission.csv ✓
```

---

## Model Performance (Out-of-Time Validation, 621,092 rows)

All metrics are computed on a strictly later time window (2019–2021 originations) than the training data (2006–2017). Positive base rates are shown alongside all performance figures per FR-033.

| Target | Model | ROC-AUC | PR-AUC | Brier | Base Rate |
|--------|-------|---------|--------|-------|-----------|
| 12-Month Default | LightGBM + Isotonic Cal. | **0.901** | **0.616** | 0.014 | 2.66% |
| 3-Month Deterioration | LightGBM + Isotonic Cal. | **0.893** | **0.601** | 0.017 | 3.15% |
| 6-Month Deterioration | LightGBM + Isotonic Cal. | **0.857** | **0.532** | 0.026 | 4.29% |
| 12-Month Prepayment | LightGBM + Isotonic Cal. | 0.638 | 0.287 | 0.139 | 17.9% |

Source: `artifacts/train/models_manifest.json` (run `run_20260828_160319_49a47ef6`)

---

## Submission File

- **756,520 rows** (one per scored loan-month)
- **13 columns**: `loan_id`, `reporting_month`, `next_3m_delinquency_prob`, `next_6m_delinquency_prob`, `next_12m_default_prob`, `next_12m_prepayment_prob`, `next_state`, `exception_required`, `exception_type`, `anomaly_score`, `top_drivers`, `recommended_action`, `confidence`
- Schema validation: **PASSED** (`artifacts/submission/submission_manifest.json`)
- Scoring window: 2023–2025 reporting months

---

## Project Structure

```
d:\Intain\
├── src/lpie/               # Source package
│   ├── stages/             # 14 pipeline stages
│   ├── models/             # GBDT, baseline, calibration, multistate
│   ├── features/           # Vectorized feature builders
│   ├── labels/             # Outcome definitions (no leakage)
│   ├── anomaly/            # IsolationForest + deterministic rules
│   ├── explain/            # TreeSHAP global + local
│   ├── survival/           # Competing-risk CIF
│   ├── scenario/           # Macro stress simulation
│   ├── llm/                # Grounded LLM provider + offline fallback
│   ├── data/               # Reader, sentinels, decoder, sampler
│   ├── conf/               # YAML config loader + validator
│   └── store/              # Deterministic artifact store + manifest
├── config/                 # pipeline.yaml, splits.yaml, scenarios.yaml, etc.
├── tests/
│   ├── unit/               # 27 unit tests
│   ├── contract/           # 4 contract tests (schema, sourcing, leakage)
│   └── integration/        # 3 integration tests (e2e, determinism, no-LLM)
├── specs/001-loan-performance-intelligence/
│   ├── spec.md             # Feature specification (74 FRs, 26 SCs)
│   ├── plan.md             # Architecture plan
│   └── tasks.md            # 112 implementation tasks
├── docs/
│   ├── ai-development-log.md
│   └── data-provenance.md
├── artifacts/              # Generated by pipeline (not committed)
└── data/raw/               # Freddie Mac R47 files (not committed)
```

---

## Data

- **Source**: Freddie Mac Single-Family Loan-Level Dataset Release 47 (R47)
- **Vintages**: 2006, 2007, 2012, 2015, 2020, 2021
- **Raw volume**: ~2 GB performance records + ~36 MB origination
- **Working population**: Sampled at whole-loan level (seed=42) — no loan appears partially
- **Sentinel handling**: `credit_score=9999`, `dti=999`, `ltv=999` treated as missing (not numeric extremes)
- **Administrative removals**: 3,572 loans excluded from label population (not defaults, not payoffs)

---

## Disqualification Safeguards (§13)

| §13 Condition | Safeguard |
|---|---|
| Only uses LLM for prediction | `test_no_llm_on_submission_path.py` — static graph assertion |
| Does not train a non-LLM model | LightGBM + Logistic baseline trained before any LLM call |
| Random splits leaking same loan | `test_split_disjointness.py` — temporal windows verified disjoint |
| Leaks target labels into features | `test_leakage_guard.py` — no target column in feature matrix |
| No reproducible code | Single-command pipeline, `test_determinism.py` |
| No evaluation metrics | PR-AUC, ROC-AUC, Brier, ECE per target in `models_manifest.json` |
| Cannot explain model behavior | TreeSHAP global + local attribution per loan-month |
| LLM narratives without grounding | Grounding validator rejects unsupported claims; see `test_grounding_validator.py` |
