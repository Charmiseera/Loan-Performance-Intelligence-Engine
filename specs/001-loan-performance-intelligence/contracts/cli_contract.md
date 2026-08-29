# CLI Contract

The headless CLI is the source of truth for all computation (Constitution: Technology & Data
Constraints). Every deliverable must be producible without launching the Streamlit app.

Entry point: `python -m lpie`

## `run` — the one command

```bash
python -m lpie run --config config/pipeline.yaml
```

This is the command FR-063 and SC-001 refer to. With a populated `data/raw/` and no prior artifacts,
it must produce every declared deliverable with no manual step.

| Option | Default | Meaning |
|---|---|---|
| `--config PATH` | `config/pipeline.yaml` | Root config. All other config files are referenced from it. |
| `--stages LIST` | all enabled | Comma-separated stage names to run. Missing upstream artifacts are an error, not an implicit rerun — a silent cascade would make "which run produced this number" unanswerable. |
| `--from STAGE` | — | Run this stage and everything downstream of it. |
| `--force` | off | Re-run stages whose outputs already exist. Without it, existing complete outputs are reused. |
| `--seed INT` | from config | Override the root seed. Recorded in the manifest as an override. |
| `--out DIR` | `artifacts/` | Artifact root. |
| `--fail-fast / --no-fail-fast` | `--fail-fast` | Whether a stage failure aborts the run. |

**Exit codes** — distinct, because "the pipeline failed" and "the pipeline ran and the output is
invalid" require different responses:

| Code | Meaning |
|---|---|
| 0 | All requested stages succeeded and submission validation passed. |
| 1 | A stage raised. |
| 2 | Configuration invalid (unknown key, missing file, bad split boundary, embargo narrower than the largest horizon). |
| 3 | A gate failed: leakage audit non-zero, or submission contract violated. The run completed but its output must not be submitted. |
| 4 | Required input data absent from `data/raw/`. |

Exit code 3 exists so that a broken guarantee is loud. A run that produced a leaky submission and
exited 0 is the worst possible outcome, so the gates get their own code.

## `validate` — check without computing

```bash
python -m lpie validate --config config/pipeline.yaml
```

Validates config, the R47 schema config against `docs/freddie-mac-r47-layout.md`, the presence and
shape of `data/raw/` files, and — if a submission exists — the submission contract. Computes nothing
and writes nothing. Exit codes 0, 2, 3, 4 as above.

## `profile` — data intelligence only

```bash
python -m lpie profile --config config/pipeline.yaml
```

Runs `ingest, contract, profile` only. This is US2's Independent Test: profiling must be runnable with
no model present.

## `explain` — local attribution on demand

```bash
python -m lpie explain --loan-id F06Q1000123 --month 202412
```

Writes a local attribution for one loan-month from the already-fitted models. Satisfies FR-053 and
SC-019. Requires a completed `train` and `features` stage; exits 1 if their artifacts are absent
rather than silently retraining.

## `app` — launch the read-only demo

```bash
python -m lpie app
```

Wraps `streamlit run app/Home.py`. The app reads `artifacts/` and cannot write, train, or alter
configuration, so it can never disagree with the documents (Principle VI).

## Global behaviour

- `--verbose` / `--quiet` control log level only. Log output is never a deliverable.
- Progress goes to stderr; machine-readable results go to files. Nothing a downstream tool needs is
  printed to stdout only.
- `GROQ_API_KEY` is read from the environment or a `.env` loaded by `python-dotenv`. It is never a CLI
  argument, so it cannot end up in shell history or a process listing.
- With no key configured, `narrate` uses the deterministic offline provider and the run still exits 0
  (FR-061, FR-073, SC-006). Absence of a key is a supported configuration, not a warning-worthy
  degradation.
