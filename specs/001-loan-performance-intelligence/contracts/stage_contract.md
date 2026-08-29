# Stage Contract

The interface every pipeline stage implements. This is the load-bearing contract in the design:
Gate G1's static guarantee, Principle V's traceability, and partial reruns all derive from the fact
that stages declare their inputs and outputs rather than discovering them at runtime.

## The protocol

```python
class Stage(Protocol):
    name: str                        # unique, stable, appears in artifact paths and the manifest
    inputs: tuple[ArtifactId, ...]   # every artifact this stage reads. Complete, or the graph lies.
    outputs: tuple[ArtifactId, ...]  # every artifact this stage writes.
    enabled_by: str                  # config key toggling the stage, e.g. "stages.survival.enabled"

    def run(self, ctx: StageContext) -> StageResult: ...
```

`StageContext` supplies the resolved config, the stage's derived seed (`seed_for(root_seed, name)`),
and an `ArtifactStore` scoped so that reads outside `inputs` and writes outside `outputs` raise. The
scoping is the point: a stage that quietly reads an undeclared artifact would invalidate the graph, so
it is made impossible rather than discouraged.

`StageResult` carries row counts, timings, peak memory, and the output artifact digests, which
`store/manifest.py` folds into `artifacts/run_manifest.json`.

## Rules

1. **Declared inputs are exhaustive.** Reading an artifact not in `inputs` raises. This is what makes
   the G1 assertion sound — if the graph can be incomplete, the transitive closure proves nothing.
2. **A stage is a pure function of its inputs plus its seed.** No wall-clock reads, no environment
   reads except through config, no network except the LLM provider in `narrate`.
3. **Outputs are written atomically.** Write to a temporary path, then rename, so an interrupted run
   leaves no half-written artifact that a later partial rerun would treat as complete.
4. **Every tabular output has an explicit sort key.** Determinism is a property of the write, not of
   the upstream computation order.
5. **Every stage that computes a number writes `metrics.json`.** Reports may only read from these.
6. **A disabled stage is skipped, not stubbed.** Downstream stages declaring its outputs as inputs are
   skipped too, transitively. This is what lets a partially-built system still run end to end: the P1
   path never declares an input produced by an unimplemented stage.

## Artifact ID namespace

An `ArtifactId` is `<stage>/<name>`, matching its path under `artifacts/`.

| Artifact ID | Format | Produced by |
|---|---|---|
| `ingest/loans` | Parquet | ingest |
| `ingest/panel` | Parquet, partitioned by vintage | ingest |
| `ingest/sample_weights` | Parquet | ingest |
| `ingest/metrics` | JSON | ingest |
| `contract/violations` | Parquet | contract |
| `contract/metrics` | JSON | contract |
| `profile/field_profiles` | JSON | profile |
| `profile/quality_scores` | Parquet | profile |
| `profile/drift` | JSON | profile |
| `profile/data_intelligence_report` | Markdown | profile |
| `profile/metrics` | JSON | profile |
| `label/labels` | Parquet | label |
| `label/termination_map` | JSON | label |
| `label/metrics` | JSON | label |
| `split/split_definition` | JSON | split |
| `split/leakage_audit` | JSON | split |
| `features/matrix_train` | Parquet | features |
| `features/matrix_valid` | Parquet | features |
| `features/matrix_score` | Parquet | features |
| `features/feature_list` | JSON | features |
| `train/models` | joblib | train |
| `train/predictions` | Parquet | train |
| `train/calibration` | JSON | train |
| `train/metrics` | JSON | train |
| `survival/incidence` | Parquet | survival |
| `survival/metrics` | JSON | survival |
| `anomaly/findings` | Parquet | anomaly |
| `anomaly/queue` | Parquet | anomaly |
| `anomaly/metrics` | JSON | anomaly |
| `explain/global_importance` | JSON | explain |
| `explain/local_attributions` | Parquet | explain |
| `explain/explainability_report` | Markdown | explain |
| `scenario/projections` | Parquet | scenario |
| `scenario/scenario_report` | Markdown | scenario |
| `llm/prompt_log` | JSONL, append-only | narrate |
| `llm/rejections` | JSONL, append-only | narrate |
| `llm/reviewer_notes` | Markdown | narrate |
| `reports/model_card` | Markdown | report |
| `submission/submission` | CSV | submit |
| `submission/validation` | JSON | submit |

## Dependency graph

```text
ingest ──> contract ──> profile
   │           │
   │           └──> label ──> split ──> features ──┬──> train ──┬──> explain ──┐
   │                                               │            │              │
   │                                               │            ├──> anomaly ──┤
   │                                               │            │              │
   │                                               └──> survival ┘             │
   │                                                            │              │
   │                                              scenario <────┘              │
   │                                                            │              │
   └────────────────────────────────────────────> narrate <─────┴──────────────┤
                                                     │                         │
                                                  report <────────────────────┤
                                                                               │
                                                  submit <────────────────────┘
```

**The property Gate G1 rests on**: `submit` declares inputs from `train`, `anomaly`, `explain`, and
`split` only. `narrate`'s outputs (`llm/*`) appear in `report`'s input set but in **no** transitive
input of `submit`. `tests/unit/test_no_llm_on_submission_path.py` asserts exactly this over the
registry, so it holds for every input rather than for the ones a test happens to exercise.

Note that `narrate` and `report` sit downstream of everything they describe and upstream of nothing
that computes. That placement is deliberate: it is what makes "the LLM never decides" a shape of the
graph instead of a promise in a docstring.

## P1 subset

The P1 vertical slice enables: `ingest, contract, profile, label, split, features, train, anomaly,
explain, narrate, report, submit`. Disabled at P1: `survival` (US4), `scenario` (US6). Since no P1
stage declares an input from either, the graph runs end to end with both off — which is the
requirement that later stories be strictly additive.
