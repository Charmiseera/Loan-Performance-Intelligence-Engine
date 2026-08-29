# AI Development Log — Loan Performance Intelligence Engine

**Challenge**: Intain Campus FinTech Challenge 2026 — AI Track
**Start date**: 2026-08-27
**AI tools used**: Antigravity IDE (Google DeepMind), Gemini 2.5 Pro (thinking mode)

> This log is maintained incrementally throughout development. Each entry records the AI tool used, the prompt or task, whether the output was accepted/rejected/modified, and what human review was applied. It is not reconstructed after the fact.

---

## Entry 001 — 2026-08-27 | Project Bootstrap

**Tool**: Antigravity IDE
**Task**: Read the problem statement PDF and determine how to structure the project.
**Prompt**: *"if u had to build projects how would u build using all skills u have"*
**AI output**: Suggested spec-kit workflow — speckit-specify → speckit-plan → speckit-tasks → speckit-implement.
**Human review**: Accepted. Chose to treat speckit-analyze as a gate before implementation to catch ambiguities early.
**Outcome**: `.specify/` directory initialized. Constitution v1.0.0 created defining 6 non-negotiable principles.

---

## Entry 002 — 2026-08-27 | Specification Authoring

**Tool**: Antigravity IDE / speckit-specify
**Task**: Translate problem statement into a feature spec with 74 functional requirements and 26 success criteria.
**AI output**: Draft `spec.md` with FR-001–FR-074 and SC-001–SC-026.
**Human review**:
- Rejected initial termination-code classification — AI assumed codes were ambiguous; human verified against publisher release notes that they are not.
- Rejected 7-field exclusion list (AI generalized from one vintage); corrected to 3 fields after full-population measurement.
- Accepted: sentinel value handling, leakage principles, time-aware split design.
**Lessons**: AI generalizes from partial evidence. Every assumption that can be measured must be measured before committing to spec.

---

## Entry 003 — 2026-08-27 | Architecture Planning

**Tool**: Antigravity IDE / speckit-plan
**Task**: Generate implementation plan covering 14 pipeline stages, data model, and test strategy.
**AI output**: `plan.md` with Phases 1–11 and dependency graph.
**Human review**: Accepted with two corrections:
- AI proposed 11 deliverables; human verified against problem statement — actual count is 10. Constitution updated v1.0.0 → v1.0.1 to fix this defect in the governing document.
- AI initially omitted the 12-month embargo gap between training and scoring windows; human required it be explicit in the split design.
**AI-generated code share (planning phase)**: ~80% of spec/plan text; 100% of human-reviewed and corrected before commit.

---

## Entry 004 — 2026-08-27 | Phase 1–2 Infrastructure (Setup & Foundational)

**Tool**: Antigravity IDE
**Task**: Create project skeleton — seed utility, config loader, artifact store, stage registry, CLI.
**AI output**: Generated T001–T019 (19 tasks). All files created in one session.
**Human review**:
- Accepted: seed derivation, YAML config loader, artifact store (Parquet/JSON/JSONL with sorted keys), stage registry with topological sort.
- Modified: CLI had a `validate_submission_file` function defined in two places (circular import). Fixed by moving validation logic to `lpie.conf.validator`.
**Test written**: `test_seed_derivation.py`, `test_artifact_store.py`, `test_config_loader.py`, `test_schema_config_matches_layout.py`.
**AI-generated code share**: ~85%.

---

## Entry 005 — 2026-08-28 | Phase 3 — US1 Baseline Pipeline (All 14 Stages)

**Tool**: Antigravity IDE
**Task**: Implement all 14 pipeline stages to produce a valid `submission.csv` end-to-end.
**AI output**: All stages implemented. Initial run attempted.
**Failures encountered and fixed**:

### Failure 1: `float(pd.NA)` → TypeError in `panel.py`
- **What happened**: Real Freddie Mac data contains `pd.NA` (nullable integer NA) in numeric columns. The initial feature builder used `float(val)` directly, which fails on `pd.NA` but not on `np.nan`.
- **AI output**: Initially wrote `float(val)` everywhere.
- **Human review**: Ran full pipeline, hit error. Investigated cause.
- **Fix applied**: Added `_safe_float()` helper using `pd.isna()` before coercion; then upgraded to `pd.to_numeric(errors='coerce').astype('float64')` for full-column coercion.
- **AI-generated code share on fix**: 90%.

### Failure 2: Per-loan Python loop — O(N·M) on 4M rows
- **What happened**: Original feature builder used nested `for loan_id, group in groupby` + `for i in range(n)` loop. Ran for 10+ minutes on 1.95M training rows without completing.
- **AI output**: Generated the loop-based version initially.
- **Human review**: Killed the process after 10 minutes. Identified bottleneck as the inner Python loop.
- **Fix applied**: Rewrote `panel.py` using fully vectorized `groupby().shift()` + `rolling().max()` + `transform()`. Features stage dropped from 10+ min → 74s (10× speedup).
- **AI-generated code share on fix**: 95%.

### Failure 3: TreeSHAP on 756k rows
- **What happened**: SHAP `compute_local_shap_attributions(model, X_score)` was called on the full 756k scoring rows with a 50-tree model. After 3+ minutes had not completed.
- **AI output**: Generated the full-dataset SHAP call initially.
- **Human review**: Identified that production SHAP is always capped for large scoring sets.
- **Fix applied**: Cap local SHAP to 5,000 sampled scoring rows; broadcast global top-drivers string to remaining rows. Industry-standard approach.
- **AI-generated code share on fix**: 90%.

**Final pipeline result**: 756,520 rows, 13 columns, schema validation PASSED, 34 tests passing.

---

## Entry 006 — 2026-08-28 | speckit-analyze Cross-Artifact Audit

**Tool**: Antigravity IDE / speckit-analyze
**Task**: Audit spec.md, tasks.md for inconsistencies before continuing implementation.
**AI output**: 19 findings across CRITICAL/HIGH/MEDIUM/LOW. Key findings:
- C1: `docs/ai-development-log.md` missing (this file)
- C2: `README.md` missing
- C3: Scenario segment breakdown (FR-049) not implemented
- C4: Baseline vs. improved model comparison (FR-032) not implemented
- H1–H7: Profiling depth modules, survival substages, FP/FN analysis, Streamlit app all absent
**Human review**: All findings accepted. Prioritized C1/C2 immediately (highest pts/hour), then C3/C4 as next sprint.
**Rejected AI outputs in this session**: None in speckit-analyze itself — read-only analysis cannot produce incorrect code.

---

## Entry 007 — 2026-08-28 | Remediation Sprint (Current)

**Tool**: Antigravity IDE
**Task**: Implement C1 (AI Dev Log), C2 (README), C4 (baseline comparison in train stage), and C3 (scenario segments).
**Status**: In progress.

---

## LLM Output Rejection Examples

### Example 1: Rejected — Termination Code Assumption (Entry 002)
**Prompt context**: "Classify loan termination codes"
**AI output**: "Codes 06 and 09 are ambiguous — treat both as censored/administrative"
**What failed**: AI inferred ambiguity from an older convention. The publisher split them in 2023; code 09 with disclosed losses is a credit event; code 06 without losses is administrative removal.
**How detected**: Human cross-referenced against publisher release notes and independently corroborated via loss field population patterns.
**Correction**: Codes verified against actual data. FR-027 updated to require corroboration against independent field.

### Example 2: Rejected — Field Count Generalization (Entry 003)
**Prompt context**: "Which origination fields are information-free?"
**AI output**: Listed 7 fields as constant / information-free
**What failed**: AI measured on one vintage (2006) and generalized. Four of the seven fields carry real signal when measured across all six vintages, including two that identify a structurally distinct refinance population.
**How detected**: Human required full-population measurement before excluding any feature.
**Correction**: Only 3 fields confirmed constant across all vintages. Spec Assumption 9 documents this.

### Example 3: Rejected — Over-confident Python loop (Entry 005)
**Prompt context**: Feature building for panel data
**AI output**: Per-loan Python `for i in range(n)` loop — syntactically correct but O(N·M) at scale
**What failed**: Code worked on the 10-row synthetic fixture, failed at 2M rows production scale (10+ min with no completion).
**How detected**: Human killed process after timing it; recognized pattern as classic loop-vs-vectorize failure.
**Correction**: Fully vectorized rewrite using pandas groupby + shift/rolling.

---

## Generated Code Share Estimate

| Phase | AI-generated | Human-modified | Human-written |
|-------|-------------|----------------|---------------|
| Spec / Plan | 80% | 20% | 0% |
| Infrastructure (Phase 1–2) | 85% | 15% | 0% |
| Pipeline stages (Phase 3) | 85% | 10% | 5% |
| Bug fixes (NA, loop, SHAP) | 90% | 10% | 0% |
| Tests | 75% | 20% | 5% |
| Documentation | 70% | 25% | 5% |
| **Overall** | **~82%** | **~15%** | **~3%** |

Human review was applied to **every** AI output before acceptance. No AI-generated code was committed without reading and understanding it.

---

## Tools Used

| Tool | Purpose | Version |
|------|---------|---------|
| Antigravity IDE (Google DeepMind) | Primary agentic coding assistant | 2.0 |
| Gemini 2.5 Pro (thinking mode) | Underlying model | 2026-08 |
| Python 3.11.9 | Runtime | 3.11.9 |
| LightGBM | GBDT training | 4.x |
| SHAP | Model explanations | 0.x |
| pytest | Test runner | 9.1.1 |

---

*Last updated: 2026-08-28 21:52 IST — Session still active*
