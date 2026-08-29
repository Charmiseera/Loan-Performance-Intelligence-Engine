# Implementation Plan: Loan Performance Intelligence Engine

**Branch**: `001-loan-performance-intelligence` | **Date**: 2026-08-27 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/001-loan-performance-intelligence/spec.md`

**Governing document**: [`.specify/memory/constitution.md`](../../.specify/memory/constitution.md) v1.0.1

> **Amendment raised by this plan.** Filling Gate G6 required enumerating the §11 deliverables, which
> exposed two defects in the constitution: it said "eleven" where the problem statement lists ten, and
> it required all of them to be pipeline-generated while four cannot be and one (the AI Development
> Log) was separately required to be hand-maintained. Amended to v1.0.1 before the gate was marked
> passing, rather than recording a pass against a document known to be wrong.

---

## Summary

Build a stage-based, artifact-emitting batch pipeline that takes raw Freddie Mac Release 47
loan-level panel files to a validated `submission.csv` plus every §11 deliverable, in one command.

The architectural centre of the design is a **stage graph with declared inputs and outputs**. Each
stage is a pure function from named input artifacts to named output artifacts, registered with its
dependencies. Three properties fall out of that structure rather than out of discipline:

1. **Principle I is provable statically.** Because `submit` declares its input artifacts, a test can
   assert that no artifact produced by the LLM stage appears anywhere in `submit`'s transitive input
   closure. That is a stronger guarantee than a runtime probe, which can only show the LLM was not
   called on the paths the test happened to exercise.
2. **Principle V is mechanical.** Every reported number is read back from the artifact that a stage
   wrote, because reports are themselves a stage whose only inputs are other stages' artifacts.
3. **Partial reruns are safe.** A stage can be re-executed from its recorded inputs without
   replaying the 19.2M-row ingest.

The second structural commitment is a **single as-of-month-aware feature layer** in which every
feature builder declares a relative month window and the registry rejects any window reaching
forward. Leakage is then testable two ways: by name screening, and empirically — perturb every panel
row strictly after the as-of month and assert the feature matrix is unchanged. The empirical test
catches leakage that name screening structurally cannot.

Approach for the P1 vertical slice: run all fourteen stages end to end with the simplest defensible
implementation of each, so a valid submission exists before any modelling sophistication is
attempted. Later user stories replace a stage's internals or add a stage; none may change the
`submit` contract.

## Technical Context

**Language/Version**: Python 3.11.9, project-local `.venv` (already created; dependencies installed
and smoke-tested). No global installs.

**Primary Dependencies**: pandas 2.3.3 / numpy 2.2.6 / pyarrow 25.0.1 (data); scikit-learn 1.9.0
(preprocessing, calibration, metrics, baselines, IsolationForest); LightGBM 4.7.0 and XGBoost 3.2.0
(gradient-boosted primary models); lifelines 0.30.3 (time-to-event); SHAP 0.51.0 (attribution);
scipy 1.17.1 / statsmodels 0.15.0 (statistical tests, drift); Streamlit 1.62.0 (read-only demo);
groq 1.7.0 (copilot provider); PyYAML 6.0.3 (config); python-dotenv 1.2.3 (env loading);
pytest 9.1.1 (tests). Exact pins in [`requirements.txt`](../../requirements.txt), full resolved tree
in [`requirements-lock.txt`](../../requirements-lock.txt).

> **Pin hazard, recorded because it is not obvious:** SHAP 0.51.0 compiles numba kernels against the
> numpy ABI. The pin is verified executing against numpy 2.2.6. Bumping numpy without re-running the
> stack smoke test can produce a pipeline that imports cleanly and fails only inside the explain
> stage.

**Storage**: Local filesystem. Raw source stays as the publisher's pipe-delimited `.txt` under
`data/raw/` (git-ignored). All intermediate and output artifacts are written under `artifacts/<stage>/`
as Parquet (tabular), JSON (metrics, manifests, audits), JSONL (append-only logs), Markdown (reports),
and one CSV (`submission.csv`). Nothing is written back into `data/raw/`. No database.

**Testing**: pytest 9.1.1. Layout `tests/{unit,contract,integration}` plus a **generated** tiny
fixture panel — `tests/fixtures/make_tiny_panel.py` synthesises it deterministically at test-collection
time so no data file is ever committed (Principle IV). Integration tests run the real stage graph
against that fixture, not against mocks, so the graph itself is under test.

**Target Platform**: Single machine, Windows 11 primary (development host), POSIX-compatible paths
throughout via `pathlib`. Headless CLI is the source of truth; Streamlit is a read-only consumer.

**Project Type**: Batch data/ML pipeline exposed as a CLI, plus a read-only multi-page demo app.
Single Python package, no service boundary.

**Performance Goals** *(these are budgets, not measurements — nothing here has been measured yet,
and each will be replaced by a measured figure in the run manifest once the pipeline first executes)*:

- Ingest streams all 12 files in bounded memory: peak RSS budget 4 GB for the whole run.
- Full P1 run from raw data to validated submission: budget 30 minutes.
- Stage re-run from cached upstream artifacts: budget 2 minutes for any single non-ingest stage.

**Constraints**:

- **Ingest must be chunked.** 19,248,196 monthly rows across ~2.0 GB of pipe-delimited text cannot
  be read whole and then held alongside model training. The reader streams with `chunksize` and
  admits rows by loan-id membership in a pre-computed sample.
- **Dtypes must be narrowed at read time**, not after. Reading 35 pipe-delimited columns at pandas
  defaults costs several times the necessary footprint; the schema config carries an explicit dtype
  per field so narrowing happens in the reader.
- **Sentinel handling is per-field, never global.** Delinquency status `99` is a genuine
  99-months-delinquent count while origination `9999` (credit score) and `999` (DTI) are missingness
  sentinels. A global sentinel list would corrupt the label. The schema config attaches sentinels to
  fields individually.
- **Loss elements have inverted signs in Release 47** and the publisher's own loss formula no longer
  evaluates. Actual Loss (performance field 22) is used directly and never recomputed from
  components.
- **Loan Age (performance field 5) resets on modification but not on payment deferral**, so it is not
  a clean seasoning variable for the 8,391 modified loans. Seasoning is derived from the reporting
  month minus the first observed month instead, and Loan Age is retained as a separate feature with
  its reset behaviour documented.
- **Servicer is time-varying** (performance field 34 since Release 47). Any servicer segmentation is
  as-of-month aware; servicer must never be joined as a static loan attribute.
- **No published layout exists for Release 47.** The schema config is generated from
  [`docs/freddie-mac-r47-layout.md`](../../docs/freddie-mac-r47-layout.md) and a contract test asserts
  the config still agrees with that document, so a silent drift between the two is caught.

**Scale/Scope**: 300,000 loans / 19,248,196 source monthly rows across 6 vintages (2006, 2007, 2012,
2015, 2020, 2021), reporting months 200601–202603. Working population reduced by two-level sampling
(see [research.md](./research.md) §2). 74 functional requirements, 26 success criteria, 8 user
stories, 14 pipeline stages, 6 mandatory enforcement tests.

**Unknowns**: None marked NEEDS CLARIFICATION. Every open question at spec time was resolved into a
recorded assumption (spec §Assumptions 1–13) or into a Phase 0 research decision. Two residual
*factual* unknowns are declared rather than hidden: the source field names at origination position 31
and performance position 35 rest on inference because the publisher has not released an R47 layout.
Neither is used as a feature and both are constant in the data, so exposure is confined to naming.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

The constitution (§Development Workflow & Quality Gates) requires this section to answer six gates,
each with a specific file or test. Initial evaluation below; post-design re-evaluation follows
Phase 1.

### G1 (Principle I — ML-First, the LLM Never Decides): **PASS**

*Which non-LLM model owns each submission column, and which test proves no LLM is on that path?*

| Submission column group | Owning model | Module | LLM involvement |
|---|---|---|---|
| Deterioration probabilities (3m, 6m) | Calibrated LightGBM classifier, logistic-regression baseline | `models/gbdt.py`, `models/baseline.py` | none |
| Default probability (12m) | Calibrated LightGBM classifier | `models/gbdt.py` | none |
| Prepayment probability (12m) | Calibrated LightGBM classifier | `models/gbdt.py` | none |
| Next state | Multinomial classifier over observed states | `models/multistate.py` | none |
| Anomaly score | IsolationForest + deterministic rule score, combined by documented rule | `anomaly/` | none |
| Exception required / exception type | Rule engine + supervised classifier | `anomaly/` | none |
| Top drivers | SHAP local attribution of the owning model | `explain/` | none |
| Recommended action | Deterministic decision table over model outputs and rule flags | `anomaly/actions.py` | none |
| Confidence | Model-derived interval / margin, method named per column | `models/uncertainty.py` | none |

Enforcement is two independent mechanisms, deliberately not one:

1. **Static graph assertion** — `tests/unit/test_no_llm_on_submission_path.py` walks the stage
   registry and asserts no artifact produced by the `narrate` stage appears in the transitive input
   closure of `submit`. This holds for all inputs, not just those a test exercises.
2. **Runtime absence** — `tests/integration/test_pipeline_without_llm.py` (FR-073, SC-006) runs the
   full graph with the provider disabled and asserts a valid submission is still produced.

Every generated artifact is labelled a recommendation by construction: `llm/promptlog.py` stamps the
label into the artifact envelope, so an unlabelled generated artifact cannot be written (FR-060,
SC-023).

### G2 (Principle II — Leakage Containment): **PASS**

*Where are split boundaries defined, and which test enforces target exclusion and temporal disjointness?*

- **Defined in** `config/splits.yaml` as month boundaries plus an explicit `embargo_months` equal to
  the maximum label horizon (12).
- **Materialised by** `stages/split.py` into `artifacts/splits/split_definition.json` and
  `artifacts/splits/leakage_audit.json` — per-split month range, row and loan counts, boundary
  overlap counts, embargo width, and the feature-name screening result (FR-070, SC-005).
- **The embargo is the part that is easy to get wrong and is therefore made explicit.** An as-of month
  `m` carries labels resolved from months up to `m + 12`. Without a 12-month gap between windows, a
  training row's *label window* overlaps the next window's *as-of months* — leakage that no
  row-disjointness check detects. The split stage rejects any configuration whose embargo is narrower
  than the largest configured horizon.
- **Tests**: `tests/unit/test_split_disjointness.py` (FR-070) asserts windows are ordered, disjoint,
  and embargoed by at least the maximum horizon. `tests/unit/test_leakage_guard.py` (FR-069) asserts
  both that no outcome-named or outcome-derived column reaches a fitted estimator **and** that
  perturbing every panel row strictly after the as-of month leaves the feature matrix byte-identical.
- **Mechanical prevention, not just detection**: `features/registry.py` requires every feature builder
  to declare a relative window `(lo, hi)` and refuses registration when `hi > 0`. Preprocessing
  statistics are fit inside a scikit-learn `Pipeline` fitted on the training split only, so a
  full-panel fit is not expressible without deleting code (FR-022).

### G3 (Principle III — Grounded LLM Governance): **PASS**

*Where is the prompt log written, and what validator rejects ungrounded output?*

- **Prompt log**: `artifacts/llm/prompt_log.jsonl`, append-only, written by `llm/promptlog.py`. One
  record per call with UTC timestamp, provider, model identifier, full rendered prompt, full raw
  response, token counts, latency, the grounding context supplied, and the accept/reject decision
  (FR-058, SC-020).
- **Validator**: `llm/grounding.py`. Extracts numeric claims and entity references from generated
  text and resolves each against the grounding context that was actually supplied. An unresolvable
  claim is a rejection, written to `artifacts/llm/rejections.jsonl` and never rendered (FR-059,
  SC-021).
- **Test**: `tests/unit/test_grounding_validator.py` (FR-074) injects a fabricated figure into
  otherwise valid generated text and asserts rejection plus absence from every reviewer-facing
  artifact.
- **Model identifier is configuration** in `config/llm.yaml`; `GROQ_API_KEY` is read from the
  environment only. `llm/offline_provider.py` satisfies the same interface with deterministic
  templated output, so the repository runs with no credentials (FR-061).
- **Curated rejection collection**: `docs/llm-failure-log.md`, maintained during development with
  annotated examples of wrong, vague, or overconfident output (FR-062, SC-022).

### G4 (Principle IV — Reproducibility by Construction): **PASS**

*What is the single command, where is the seed threaded, and where are versions pinned?*

- **Single command**: `python -m lpie run --config config/pipeline.yaml` (FR-063, SC-001). Stage
  subsets are addressable via `--stages` for development but the full run needs no arguments beyond
  the config path.
- **Seed**: one integer in `config/pipeline.yaml`, threaded explicitly by `util/seed.py`, which
  derives per-stage child seeds deterministically from `(root_seed, stage_name)`. No component reads
  a global RNG; every splitter, sampler, estimator, and simulator receives its seed as an argument.
  Deriving child seeds rather than reusing one value means adding a stage cannot silently change
  another stage's stream.
- **Pins**: `requirements.txt` (direct, exact) and `requirements-lock.txt` (full resolved tree), both
  committed, installed into `.venv`.
- **Determinism**: all written tables carry explicit sort keys via `store/store.py`; parquet is
  written with a fixed row-group size and no timestamp metadata. Test
  `tests/integration/test_determinism.py` (FR-071, SC-002) asserts two seeded runs produce a
  byte-identical submission.
- **Config, not literals**: schema, paths, split boundaries, hyperparameters, scenario assumptions,
  and the R47-position → §7-vocabulary field-name translation all live under `config/`. Swapping to an
  organiser-supplied data pack is a config change (FR-002).
- **Data stays out of git**: already enforced by `.gitignore`; provenance is in
  [`docs/data-provenance.md`](../../docs/data-provenance.md).

### G5 (Principle V — Honest Reporting & Declared Limits): **PASS**

*Which artifact does each reported metric come from, and where is the model card generated?*

- Every metric is written to a per-stage JSON artifact (`artifacts/<stage>/metrics.json`) by the stage
  that computed it. `stages/report.py` renders all Markdown deliverables **only** by looking up keys
  in those artifacts; it has no other data input (FR-065, SC-007).
- **Model card** generated by `stages/report.py` into `artifacts/reports/model_card.md`, covering
  objective, data, features, model type, validation method, metrics, leakage controls, limitations,
  and known failure modes (FR-056, SC-024).
- **Enforcement with teeth**: report templates live in `templates/` and
  `tests/contract/test_report_numbers_are_sourced.py` asserts no template contains a literal numeric
  token outside a substitution placeholder. A hand-typed metric therefore fails the build rather than
  relying on discipline.
- Metrics are written together with the split they came from and the positive-class count and rate
  behind them, so a bare score cannot be reported without its denominator.

### G6 (Principle VI — Deliverables Are Build Outputs): **PASS**

*Which pipeline stage writes each §11 deliverable, and what validates the submission contract?*

§11 lists **ten** deliverables. Six are computed artifacts and are bound by Principle VI's
code-generation rule; four are authored. The distinction is the constitution's, as amended in v1.0.1.

**Computed — written by a stage, never by hand:**

| §11 deliverable | Written by | Path |
|---|---|---|
| `submission.csv` | `stages/submit.py` | `artifacts/submission/submission.csv` |
| Model card | `stages/report.py` | `artifacts/reports/model_card.md` |
| Data intelligence report | `stages/profile.py` | `artifacts/profile/data_intelligence_report.md` |
| Explainability report | `stages/explain.py` | `artifacts/explain/explainability_report.md` |
| Scenario report | `stages/scenario.py` | `artifacts/scenario/scenario_report.md` |
| LLM copilot demo output | `stages/narrate.py` | `artifacts/llm/reviewer_notes.md` |

**Authored — incremental, not generated:**

| §11 deliverable | Where | Rule |
|---|---|---|
| GitHub repository | this repository | — |
| Reproducible notebook or scripts | `src/lpie/`, `config/`, `README.md` | the one command is the workflow (FR-063) |
| AI Development Log | `docs/ai-development-log.md` | MUST be incremental, never reconstructed (FR-067, SC-025) |
| Five-minute demo video | recorded against `app/` and `artifacts/` | follows §14's flow over real artifacts |

**Supporting artifacts that back the above** (not §11 items, listed because Principle V requires every
reported number to have a source): `artifacts/<stage>/metrics.json` per computing stage,
`artifacts/run_manifest.json` (config hash, seed, library versions, per-stage timings, peak memory),
`artifacts/splits/leakage_audit.json`, `artifacts/llm/prompt_log.jsonl`,
`artifacts/llm/rejections.jsonl`.

- **Submission contract**: `contracts/submission_schema.json` is the machine-readable contract.
  `stages/submit.py` validates against it and fails the run on any violation; the same file backs
  `tests/contract/test_submission_contract.py` (FR-066, FR-072, SC-003). One contract file, two
  consumers — the test and the runtime cannot diverge.
- **The contract is authored, and that is a finding, not a convenience.** The problem statement
  contains no submission schema — see *Declared tensions* item 4 below.

### Declared tensions (mitigated, not violations)

Recorded here because they are the places where an unexamined choice would breach a principle later.

1. **Enriching the training sample with rare positives vs. honest base-rate reporting (Principle V).**
   Retaining all 9,117 credit-event loans while subsampling the other 290,883 raises in-sample
   prevalence above population prevalence. Mitigation: inclusion probabilities are recorded per loan;
   calibration and all reported metrics are computed on a **naturally-weighted** holdout drawn without
   enrichment; both sample and population base rates are reported side by side. Detail in
   [research.md](./research.md) §2.
2. **A constructed reconciliation fixture vs. fabricated data (Principle V).** The source has one
   authoritative record per loan-month, so genuine cross-source conflict does not exist in it. The
   fixture is generated on top of *real* servicer-transfer patterns and labelled constructed in both
   its own header and the model card (FR-007, SC-026).
3. **`.gitignore` globally ignores `*.csv`.** A committed submission *template* would be silently
   untracked. Mitigation: the contract is expressed as JSON Schema in `contracts/`, not as a sample
   CSV, which is both stronger and immune to the ignore rule.
4. **The submission schema is authored, because the problem statement does not contain one
   (Principle V).** Verified by full read of all six pages: §11 names `submission.csv` and describes
   it only as "Predictions in the required format"; the sole enumeration anywhere is a prose phrase in
   §6 — "probabilities, next state, exception type, anomaly score, top drivers, action, and
   confidence" — with no identifier-form column names, no order, no dtypes, no value ranges, no
   allowed-value sets, and no stated row key. §7's field list is introduced as "Example fields
   include" and its target sentence as "should include", so both are explicitly illustrative rather
   than normative. The document also prints `submission_template.csv` in §6 but `submission.csv` in
   §9 and §11, and prints "next state"/"exception type" with spaces in §6 against
   `next_state`/`exception_type` with underscores in §7, without reconciling either.
   Mitigation: `contracts/submission_schema.json` derives every column from the seven §7 target names
   plus the seven §6 output items, is declared **authored** in its own header and in the model card,
   and is structured so that an organiser-supplied template supersedes it as a configuration change.
   Presenting an authored schema as if it were given would be the exact Principle V failure this
   project is built to avoid.
5. **No horizon, state vocabulary, or exception taxonomy is defined by the problem statement.** The
   `3m`/`6m`/`12m` substrings appear only inside the target *names*; no sentence defines them.
   `next_state` has no enumerated state space and `exception_type` no taxonomy anywhere in the
   document. Mitigation: each is defined in [research.md](./research.md) §4 and §14 with its rationale,
   recorded in `config/field_mapping.yaml`, and labelled a stated definition in the model card.

## Project Structure

### Documentation (this feature)

```text
specs/001-loan-performance-intelligence/
├── plan.md              # This file (/speckit-plan command output)
├── spec.md              # Feature specification
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/           # Phase 1 output (/speckit-plan command)
│   ├── submission_schema.json
│   ├── artifact_manifest_schema.json
│   ├── cli_contract.md
│   └── stage_contract.md
├── checklists/
│   └── requirements.md  # Spec quality checklist (complete)
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
config/                          # All tunable inputs. Principle IV: no literals in code.
├── pipeline.yaml                # seed, paths, stage toggles, working-population targets
├── schema_r47.yaml              # positional field map, dtypes, per-field sentinels, decode maps
├── field_mapping.yaml           # R47 field name -> problem statement §7 vocabulary
├── splits.yaml                  # month boundaries + embargo_months
├── validation_rules.json        # deterministic data-quality rules (FR-009)
├── scenarios.yaml               # stated stress assumptions (FR-047)
├── features.yaml                # enabled feature specs per model
└── llm.yaml                     # provider, model id, grounding thresholds

src/lpie/
├── __main__.py                  # python -m lpie
├── cli.py                       # run / stage / validate subcommands
├── conf/
│   ├── loader.py                # YAML -> typed config, fails loudly on unknown keys
│   └── models.py                # config dataclasses
├── stages/
│   ├── registry.py              # STAGE_REGISTRY, dependency graph, topological order
│   ├── base.py                  # Stage protocol: declared inputs, outputs, run()
│   ├── ingest.py                # 01 chunked read + whole-loan sample -> parquet
│   ├── contract.py              # 02 structural validation + rule evaluation
│   ├── profile.py               # 03 data intelligence (US2)
│   ├── label.py                 # 04 outcome construction from ZB + delinquency
│   ├── split.py                 # 05 time-aware split + embargo + leakage audit
│   ├── features.py              # 06 as-of feature matrices per split
│   ├── train.py                 # 07 baseline + improved per outcome (US3)
│   ├── survival.py              # 08 competing-risk time-to-event (US4)
│   ├── anomaly.py               # 09 rules + IsolationForest + reviewer queue (US5)
│   ├── explain.py               # 10 SHAP global + local (US7)
│   ├── scenario.py              # 11 base / adverse / high-prepayment (US6)
│   ├── narrate.py               # 12 grounded LLM reviewer notes (US8)
│   ├── report.py                # 13 model card + all Markdown deliverables
│   └── submit.py                # 14 assemble + validate submission.csv
├── data/
│   ├── reader.py                # streaming pipe-delimited reader, positional per schema
│   ├── sentinels.py             # per-field sentinel policy
│   ├── decode.py                # coded value -> documented vocabulary
│   └── sample.py                # two-level stratified sampler, records weights
├── features/
│   ├── registry.py              # feature specs; rejects forward-looking windows
│   ├── asof.py                  # as-of-month contract enforcement
│   ├── panel.py                 # lag / rolling / trend builders
│   └── static.py                # origination attribute builders
├── labels/
│   ├── termination.py           # zero-balance code -> payoff / credit / remove
│   └── outcomes.py              # horizon-based target definitions
├── models/
│   ├── baseline.py              # logistic regression / majority reference
│   ├── gbdt.py                  # LightGBM primary, XGBoost comparison
│   ├── multistate.py            # next-state multinomial
│   ├── calibration.py           # isotonic / Platt on naturally-weighted holdout
│   ├── uncertainty.py           # per-column confidence method
│   └── metrics.py               # PR-AUC, recall@precision, Brier, with denominators
├── survival/
│   ├── cause_specific.py        # per-cause hazard
│   └── incidence.py             # cumulative incidence under competing risks
├── anomaly/
│   ├── rules.py                 # deterministic rule engine
│   ├── learned.py               # IsolationForest scoring
│   ├── combine.py               # documented rule + statistical fusion
│   ├── actions.py               # deterministic action decision table
│   └── queue.py                 # prioritised reviewer queue
├── explain/
│   ├── global_importance.py
│   └── local_attribution.py
├── scenario/
│   ├── assumptions.py           # loads and labels stated assumptions
│   └── project.py               # segment projections + reconciliation
├── llm/
│   ├── provider.py              # abstract interface
│   ├── groq_provider.py         # model id from config, key from environment
│   ├── offline_provider.py      # deterministic fallback
│   ├── grounding.py             # citation + numeric-claim validator
│   └── promptlog.py             # append-only log; stamps recommendation label
├── store/
│   ├── store.py                 # artifact read/write, deterministic sort, parquet options
│   └── manifest.py              # run manifest: config hash, seed, versions, timings
└── util/
    ├── seed.py                  # root seed -> deterministic per-stage child seeds
    └── logging.py

templates/                       # Report templates; no literal numbers permitted
├── model_card.md.j2
├── data_intelligence_report.md.j2
├── explainability_report.md.j2
└── scenario_report.md.j2

tests/
├── conftest.py
├── fixtures/
│   └── make_tiny_panel.py       # generates a synthetic mini-panel; nothing committed
├── unit/
│   ├── test_leakage_guard.py            # FR-069  (name screen + forward-perturbation)
│   ├── test_split_disjointness.py       # FR-070
│   ├── test_grounding_validator.py      # FR-074
│   ├── test_no_llm_on_submission_path.py
│   ├── test_termination_mapping.py
│   ├── test_sentinels.py
│   ├── test_asof_features.py
│   └── test_seed_derivation.py
├── contract/
│   ├── test_submission_contract.py      # FR-072
│   ├── test_schema_config_matches_layout.py
│   └── test_report_numbers_are_sourced.py
└── integration/
    ├── test_pipeline_end_to_end.py
    ├── test_determinism.py              # FR-071
    └── test_pipeline_without_llm.py     # FR-073

app/                             # Streamlit: read-only consumer of artifacts/
├── Home.py
└── pages/
    ├── 1_Data_Intelligence.py
    ├── 2_Predictions.py
    ├── 3_Time_To_Event.py
    ├── 4_Reviewer_Queue.py
    ├── 5_Scenarios.py
    ├── 6_Explainability.py
    └── 7_Copilot.py

artifacts/                       # git-ignored; every stage writes here
data/raw/                        # git-ignored; publisher files as downloaded
docs/                            # provenance, R47 layout, AI development log, failure log
```

**Structure Decision**: Single Python package (`src/lpie`) with a stage registry, plus a separate
read-only `app/` and a `config/` tree. Rejected alternatives: a notebook-driven layout (cannot satisfy
FR-063's one-command requirement or Principle II's shared-feature-layer constraint); a
backend/frontend split (there is no service boundary — the app reads the same filesystem the CLI
writes, which is exactly what Principle VI requires so the two can never disagree); one module per
judging criterion (would duplicate the feature layer across criteria, which Principle II's
"shared transformation layer" forbids).

The `stages/` package is deliberately flat and numbered in comments rather than nested by user story,
because a stage's position in the dependency graph is a property of data flow, not of which story
motivated it. US4's `survival.py` and US6's `scenario.py` sit beside P1 stages and are toggled off in
`config/pipeline.yaml` until implemented, so a partially-built system still runs end to end.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No principle violations. All six gates pass with named artifacts and named tests, and the three
places where a violation could plausibly arise are recorded under *Declared tensions* above with the
mitigation that keeps each inside the principle.
