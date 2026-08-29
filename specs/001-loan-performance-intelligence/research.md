# Phase 0 Research: Loan Performance Intelligence Engine

**Plan**: [plan.md](./plan.md) | **Spec**: [spec.md](./spec.md) | **Date**: 2026-08-27

Every decision below was open at the end of `/speckit-specify`. None is marked NEEDS CLARIFICATION
in the plan because each resolved to a defensible choice here. Where a choice is a judgement call
rather than a forced move, the rejected alternative is named so the decision can be reversed on
evidence rather than re-argued from scratch.

Numbers cited are measured, from [`docs/data-provenance.md`](../../docs/data-provenance.md) and
[`docs/freddie-mac-r47-layout.md`](../../docs/freddie-mac-r47-layout.md). Numbers that are *targets*
are labelled as such.

---

## 1. Pipeline orchestration: a stage registry, not a workflow engine

**Decision**: An in-process stage registry. Each stage is an object declaring `name`,
`inputs: list[ArtifactId]`, `outputs: list[ArtifactId]`, and `run(ctx) -> None`. `stages/registry.py`
topologically sorts them and the CLI executes the order. Artifacts are files under
`artifacts/<stage>/`; a run manifest records config hash, seed, library versions, and per-stage
timings.

**Rationale**: The declared-inputs property is what makes Gate G1 statically provable — a test can
assert the `narrate` stage's outputs are absent from `submit`'s transitive input closure. A plain
sequence of scripts has no graph to interrogate, so the same guarantee would degrade to a runtime
probe that only covers the paths a test happens to exercise. The registry costs roughly one small
module and buys a structural guarantee against the single highest-severity disqualification condition.

**Alternatives considered**:

- **Prefect / Airflow / Dagster** — real orchestrators, but they add a scheduler, a server, or a
  daemon to a single-machine batch job, and none of them is needed to satisfy FR-063's one-command
  requirement. Constitution's complexity discipline says prefer the simplest construct that satisfies
  the principle.
- **DVC / Make** — would give caching and a dependency graph for free, but the graph lives in a
  separate DSL that Python tests cannot introspect, which is exactly the property G1 needs.
- **A single `main.py` calling functions in order** — simplest of all, and rejected only because of
  G1. Worth recording: if G1 could be satisfied another way this would be the right answer.

---

## 2. Working-population sampling: enrich once at loan level, handle imbalance in the model

This is the most consequential decision in Phase 0, because getting it wrong either destroys the rare
class or destroys the base rate.

**The constraint that forces the design**: 19,248,196 monthly rows across 300,000 loans, averaging
64.2 rows per loan. The problem statement suggests a working volume of 250,000–1,000,000 rows. Naively
sampling loans to hit 1,000,000 *panel* rows allows only ~15,600 loans, which at the measured 3.08%
credit-event rate yields roughly 480 credit events — too thin to fit, calibrate, and evaluate a rare
event across a three-way temporal split.

**Decision**: two levels, with only the first one enriching.

- **Level 1 — whole-loan stratified sample.** Strata are `vintage × terminal bucket`
  (6 × 4 = 24 cells, buckets being prepay / credit event / administrative removal / censored).
  **All 9,117 credit-event loans are retained.** The remaining 290,883 are sampled at the rate needed
  to reach the configured loan target (default 90,000 loans), so ≈ 27.8% of non-credit loans. Whole
  loans, never rows, so every retained loan has a complete history and the as-of feature layer never
  sees a hole. Per-loan inclusion probability is written to
  `artifacts/ingest/sample_weights.parquet`.
- **Level 2 — as-of-month subsample, uniform.** From the retained panel (≈ 5.8M loan-months) a
  uniform random subsample of as-of months per loan, stratified by split window, lands the modelling
  matrix inside the suggested band (target ≈ 600,000 rows). **This level does not enrich** — it does
  not preferentially keep positive rows.

Class imbalance is then handled at the estimator (class weights / `scale_pos_weight`) rather than by
further sampling. Both the sample base rate and the population base rate are reported for every
outcome.

**Rationale**: Level 1 enrichment is unavoidable — a 3.08% event cannot survive an 18× volume
reduction untouched. Level 2 enrichment is *avoidable*, so it is avoided: every additional sampling
distortion is another correction that has to be right for the calibration story to hold. Keeping
level 2 uniform means the only prevalence distortion in the system is a single known loan-level
factor (≈ 3.3×, from 3.08% population to ≈ 10.1% in-sample), which is recorded rather than inferred.

**Honest-reporting mitigation (Principle V)**: calibration and all headline metrics are computed on a
holdout drawn **without** level-1 enrichment — a naturally-weighted sample from the same score window.
Enrichment therefore affects what the model is *trained* on, never what its performance is *claimed*
to be. `artifacts/split/split_definition.json` records both the enriched training population and the
naturally-weighted evaluation population with their respective base rates.

**Alternatives considered**:

- **Sample loans uniformly at ~15,600 to hit the band directly** — preserves the base rate perfectly
  and was rejected because ~480 credit events split across train/valid/score leaves too few positives
  in the score window to report a stable PR-AUC. The band is a suggestion in the problem statement;
  the rare class is a measured fact.
- **Retain all 300,000 loans and subsample only as-of months** — attractive because it distorts
  nothing, but requires the full 19.2M-row panel resident for feature construction. Rejected on the
  4 GB memory budget, not on principle. Recorded as the preferred design if the budget is ever raised.
- **SMOTE / synthetic minority oversampling** — rejected outright. Synthesising loan-months in a
  panel with autocorrelated within-loan structure fabricates histories that never existed, which sits
  badly beside Principle V and would be indefensible under questioning.
- **Keep all positive rows at level 2 as well** — deferred, not rejected. If the rare class proves too
  thin after level 1, this is the next lever, and it comes with an obligation to add inverse-probability
  weighting to every metric.

---

## 3. Temporal split: three windows separated by a 12-month embargo

**Decision**: split by as-of month with an explicit embargo equal to the longest label horizon.
Default boundaries in `config/splits.yaml`:

| Window | As-of months | Label resolution reaches | Length |
|---|---|---|---|
| Train | 200601 – 202103 | 202203 | 183 months |
| *(embargo)* | 202104 – 202203 | — | 12 months |
| Validation | 202204 – 202303 | 202403 | 12 months |
| *(embargo)* | 202304 – 202403 | — | 12 months |
| Score | 202404 – 202503 | 202603 (data end) | 12 months |

**Rationale**: this is the leakage most often missed. An as-of month `m` carries labels resolved from
months up to `m + 12`. Without a gap, a *training* row's label window overlaps the *next* window's
as-of months, so the model is selected using outcomes that were observable inside the evaluation
period. No row-level or loan-level disjointness check detects this, because the rows themselves are
disjoint — only the label windows overlap. The embargo months are used for label resolution only and
never appear as as-of months. `stages/split.py` refuses any configuration whose embargo is narrower
than the largest configured horizon, so the invariant cannot be broken by editing config.

The score window ends at 202503 because 202603 is the last observed month and a 12-month horizon
needs 12 months of lookahead. Months 202504–202603 are lookahead-only.

**Consequence worth stating**: the score window's population is not a random sample of the training
population. 2006-vintage loans surviving to 202404 are 18-year seasoned survivors; 2020/2021-vintage
loans are young. That is genuine covariate shift and is the honest input to US2's drift analysis
(FR-016) rather than a defect to be sampled away.

**Alternatives considered**:

- **No embargo, adjacent windows** — the conventional and wrong choice. Rejected on Principle II.
- **Loan-disjoint split (group split by loan id)** — rejected because the constitution requires
  time-aware splitting and §13 names random loan-level splitting as a disqualification condition. A
  loan legitimately appears in multiple windows at different ages; that is the panel structure, not
  leakage, provided the as-of rule holds.
- **Rolling-origin / walk-forward evaluation** — better use of data and a genuine improvement, but it
  multiplies the number of fitted models and metric surfaces. Deferred to a later story; the fixed
  three-way split is what P1 needs.

---

## 4. Outcome definitions and the censoring rule

**Decision**: each outcome is an explicit function of post-as-of records, with a three-valued result —
positive, negative, or **unlabelled**. Unlabelled rows are excluded from that outcome's training
population (FR-028) rather than coerced to zero.

Delinquency is measured by `dq_months(status)`: the integer value of the two-character status code,
with `RA` (REO acquisition) mapped to a terminal value above every numeric code. `99` in this field is
a genuine 99-months-delinquent count, not a sentinel.

| Outcome | Positive when, within the horizon after `m` | Horizon |
|---|---|---|
| Near-term deterioration | any month has `dq_months ≥ 1` | 3 months |
| Longer-horizon deterioration | any month has `dq_months ≥ 1` | 6 months |
| Default | a credit-event termination (`02`,`03`,`09`,`15`) occurs **or** `dq_months ≥ 6` is reached | 12 months |
| Prepayment | termination with zero-balance code `01` | 12 months |
| Next state | the loan's state at `m + 3` | 3 months |

**Default is "180+ days delinquent or credit event"**, the standard definition, chosen over
"credit event only" because credit-event realisation lags deterioration by many months — a
credit-event-only label at a 12-month horizon would be dominated by loans that were already deeply
delinquent at the as-of month, making the task partly trivial and partly unlearnable.

**Censoring rule, stated because it is an approximation and Principle V requires naming approximations**:

- **Panel ends before `m + H` with the loan still alive** → **unlabelled**. Genuinely indeterminate.
  This is what the embargo protects against needing.
- **Loan terminates inside the horizon** → termination is absorbing. Outcomes requiring the loan to be
  alive resolve to negative, with the reason recorded per row. A prepaid loan cannot subsequently
  default, so `default = 0` is a determination, not an assumption; but `deterioration = 0` for a loan
  that prepaid in month 2 of a 6-month window conflates *did not happen* with *could not happen*.
- That conflation is exactly the competing-risks problem, and it is **the stated reason US4 exists**.
  The binary classifiers approximate; the time-to-event model handles it properly. The model card
  names this as an approximation rather than leaving it implicit.
- **Administrative removals (`16`, `96`, 3,572 loans)** stay in the panel — their pre-termination rows
  are valid observations — but any outcome whose resolution window contains the removal month is
  **unlabelled**, because neither payoff nor credit event occurred. Counting them either way would
  misstate credit events by 39% in one direction or understate them in the other.

**Alternatives considered**: treating all terminations as censored (loses the prepayment signal that
is 65% of the data); coercing every indeterminate case to zero (inflates every metric and is the
textbook version of the label leakage §13 disqualifies).

---

## 5. Ingest: two passes, chunked, dtypes narrowed at read time

**Decision**: pass one streams the six origination files (300,000 rows total, cheap) to build strata
and draw the level-1 loan sample. Pass two streams each performance file with
`pandas.read_csv(..., sep='|', header=None, names=<from schema config>, dtype=<from schema config>,
chunksize=500_000)` and admits only rows whose loan id is in the sample, appending to a Parquet
dataset partitioned by vintage.

**Rationale**: the sample must be known before the expensive pass, and it can be — the origination
files carry the join key and the strata variables, and the terminal bucket comes from a cheap
projection of the performance files (loan id + zero-balance code only). Three passes total, only one
of them wide. Dtype narrowing happens in the reader because the alternative — read at defaults, then
downcast — pays the peak memory cost it is trying to avoid.

**Detail that matters**: the reader is **positional**. There is no header row and no published R47
layout, so column identity comes from `config/schema_r47.yaml`, generated from
`docs/freddie-mac-r47-layout.md`. `tests/contract/test_schema_config_matches_layout.py` asserts the
config still agrees with that document — the schema config is the one place where a silent one-column
shift would corrupt every downstream number while raising no error.

**Alternatives considered**: pyarrow CSV reader (faster, but its type inference and null handling are
harder to constrain per-field, and per-field sentinel policy is a hard requirement); Dask (adds a
scheduler for a job that fits in memory once sampled); loading everything and sampling after
(exceeds the memory budget by design).

---

## 6. Class imbalance: estimator weights, reported not assumed

**Decision**: `class_weight='balanced'` for the logistic baseline and `scale_pos_weight` set from the
training-split positive rate for LightGBM. The technique and the resulting effective weight are
written to `artifacts/train/metrics.json` (FR-033).

**Rationale**: 96.34% of monthly rows are status `00`. Weighting changes the decision threshold
implicitly, which is fine because no metric in the plan depends on the default 0.5 threshold —
PR-AUC and recall-at-fixed-precision are threshold-free or explicitly threshold-parameterised.
Weighting also leaves the training rows untouched, so it composes cleanly with §2's sampling instead
of stacking a second distortion on top.

**Alternatives considered**: random undersampling of negatives (a third prevalence distortion);
SMOTE (rejected in §2 for the same reason); focal loss (available in neither pinned booster without
a custom objective, and a custom objective is unverifiable effort for a marginal gain).

---

## 7. Calibration: isotonic on a naturally-weighted holdout

**Decision**: fit the model on the enriched training split, then fit an isotonic regression on the
validation split drawn **without** level-1 enrichment. Report reliability (predicted vs observed by
decile) before and after, on the score window (FR-035, SC-010).

**Rationale**: weighting and enrichment both shift the predicted probability scale away from
population prevalence. Calibrating against a naturally-weighted sample corrects that in one step,
without needing an analytic prior-shift offset whose derivation would have to be trusted rather than
measured. Isotonic over Platt scaling because the distortion here is a monotone prevalence shift
rather than a sigmoid mis-shape, and the validation split is large enough that isotonic's variance
cost is affordable.

**Alternatives considered**: Platt/sigmoid (fewer parameters, but assumes a functional form the
distortion does not have); analytic prior correction `p' = p·π/(p·π + (1-p)(1-π'))` — cheap and
recorded as a cross-check, but not the primary, because it corrects only the enrichment and not the
class weighting.

---

## 8. Competing risks: cause-specific hazards plus Aalen–Johansen incidence

**Decision**: per-cause Cox proportional-hazards models (lifelines `CoxPHFitter`) for covariate
effects, and `AalenJohansenFitter` for absolute cumulative incidence of prepayment and credit event
over loan age. The mandated comparison against a simpler alternative (FR-041, SC-013) is against
naive Kaplan–Meier `1 − S(t)` fitted per cause with the competing event treated as censoring.

**Rationale**: the naive comparison is not a straw man — it is the specific error the design exists to
avoid, and it is quantifiable. With 65% prepayment competing against 3% credit events, treating
prepayment as ordinary censoring overstates cumulative default incidence, and the two naive curves can
sum above one. Aalen–Johansen cannot: it is a proper decomposition of the all-cause distribution, so
SC-012's "sum to no more than one at every horizon" holds by construction rather than by luck. The
comparison therefore doubles as the evidence for the modelling choice.

**Alternatives considered**: **Fine–Gray subdistribution hazards** — the textbook answer for direct
covariate effects on cumulative incidence, and **rejected because the pinned stack has no supported
implementation** (lifelines provides cause-specific Cox and Aalen–Johansen, not Fine–Gray). Hand-rolling
it would produce a number no test could validate, which is worse than not producing it. Its absence is
declared as a limitation in the model card rather than papered over. Also considered: discrete-time
multinomial hazard on the loan-month panel — genuinely attractive since the panel is already
loan-month and it reuses the classification stack, and kept as the fallback if Cox fitting on ~90,000
loans proves too slow.

---

## 9. Anomaly detection: deterministic rules and a learned score, fused explicitly

**Decision**: `anomaly/rules.py` evaluates `config/validation_rules.json` (named, severity-tagged
conditions) to produce a rule-violation vector. `anomaly/learned.py` fits an `IsolationForest` on
training-window features only. `anomaly/combine.py` produces the final score as a documented
weighted combination of the normalised learned score and the severity-weighted rule score, with both
components retained separately so a reviewer can see which drove the flag (FR-045, SC-017).

**Rationale**: the two detect different things and must not be collapsed. Rules catch what is *known* to
be invalid — a maturity date before origination, a balance rising without a modification flag — and
are explainable by construction. The learned score catches what is merely *unusual*. Keeping both
components in the output is what makes FR-044 ("name the fields or rules responsible") answerable for
rule hits and honest for statistical hits.

**Alternatives considered**: autoencoder reconstruction error (no better on tabular data of this size
and much harder to explain); LOF (poor scaling to hundreds of thousands of rows); rules only (would
score zero on the learned half of the criterion); learned only (unexplainable, and would waste the
genuine cross-field contradictions the profiling stage already finds).

---

## 10. Explainability: SHAP TreeExplainer, with the sampling declared

**Decision**: `TreeExplainer` on the LightGBM models for both global importance (mean absolute SHAP
over a seeded sample of the score window) and local attribution on demand. Global importance is
reported alongside permutation importance so a single method's artifacts are not the only evidence
(FR-052). Local contributions plus the expected value are asserted to reconcile to the model output
within a stated tolerance (SC-019).

**Rationale**: TreeExplainer is exact for tree ensembles and fast enough to run inside the pipeline
rather than as an offline afterthought, which Principle VI requires. The reconciliation assertion is
the part worth building: it converts "we ran SHAP" into a checkable property.

**Recorded hazard**: SHAP 0.51.0's numba kernels are compiled against the numpy ABI and verified
against numpy 2.2.6 only. A numpy bump can produce a pipeline that imports fine and fails only here.

**Alternatives considered**: KernelExplainer (model-agnostic but orders of magnitude slower and
approximate — pointless when the models are trees); LIME (local only, unstable across runs, which
collides with FR-064's determinism requirement); coefficients from the logistic baseline alone
(honest but explains the baseline, not the model that produced the submission).

---

## 11. Grounding validator: resolve every numeric claim against supplied context

**Decision**: `llm/grounding.py` runs three checks on each generation, before it is shown anywhere.

1. **Numeric-claim resolution** — extract every number from the generated text (including percentages
   and currency) and require each to match a value present in the grounding context within a stated
   tolerance. Unmatched number → reject.
2. **Entity resolution** — every loan identifier, field name, and rule name mentioned must exist in the
   supplied context. Unknown entity → reject.
3. **Scope check** — the text must not contain directive language that asserts a decision rather than a
   recommendation.

Rejections are appended to `artifacts/llm/rejections.jsonl` with the failing check named, and the
deterministic template output is used instead so the pipeline never stalls on a rejection.

**Rationale**: the failure mode being defended against is a plausible-looking wrong number, which is
both the most likely LLM error on this material and the one a human reviewer is least able to catch by
reading. Extraction-and-resolution is mechanical and testable; FR-074's test injects a fabricated
figure and asserts rejection.

**Deliberate design choice**: the validator is **allow-list by resolution, not deny-list by pattern**.
A number is rejected unless it can be traced, rather than accepted unless it looks suspicious. The
inverse would fail exactly on novel fabrications.

**Alternatives considered**: LLM-as-judge self-verification (asks the same failure mode to police
itself, and adds a second ungrounded generation); embedding-similarity grounding (measures topical
relatedness, which is not the property in question — a fabricated number is highly similar to a real
one); post-hoc human review only (unauditable and does not satisfy FR-059's requirement for a
validator that runs on each generation).

---

## 12. Determinism: byte-identity is claimed for the submission only

**Decision**: FR-071/SC-002 are satisfied against `submission.csv`. Achieved by explicit sort keys
before write, fixed column order from the contract, fixed `float_format`, `lineterminator='\n'`, no
index column, and seeded/deterministic estimator settings (`deterministic=True`,
`force_row_wise=True`, fixed thread count for LightGBM; explicit `random_state` everywhere;
`util/seed.py` deriving per-stage child seeds from `(root_seed, stage_name)`).

**Rationale and honest scope limit**: byte-identity of Parquet intermediates is *not* claimed. Parquet
writers embed library-version metadata and compression can vary with thread scheduling, so asserting
byte-identity there would produce a test that fails for reasons unrelated to the property being
protected. Intermediates are instead checked by content hash of a canonical sorted projection. The
constitution asks for a determinism test on submission output; that is what is delivered, and the
narrower scope is stated rather than quietly assumed.

Per-stage child seeds rather than one shared seed, so that inserting a stage cannot shift another
stage's random stream — otherwise the determinism test starts failing on unrelated changes and gets
disabled, which is how determinism guarantees actually die.

**Alternatives considered**: one global `random_state` (fragile as above); hash-based reproducibility
across machines (LightGBM histogram construction is not portable across CPU feature sets; claiming
cross-machine byte-identity would be a claim that fails on a judge's laptop).

---

## 13. Scenario mechanism: transform features, re-score, never invent labels

**Decision**: scenarios in `config/scenarios.yaml` are named sets of stated transformations on
scenario-sensitive features (rate environment, unemployment proxy, house-price proxy, and a
prepayment-propensity multiplier). `scenario/project.py` applies the transformation to the score-window
feature matrix, re-scores the already-fitted models, and aggregates projected rates by vintage, credit
band, geography, and servicer-as-of-month. Segment projections are reconciled to portfolio totals and
the residual is reported (SC-018).

**Rationale**: re-scoring an existing model under perturbed inputs is the only mechanism here that
does not require forecasting the macro environment, which is explicitly out of scope. Every assumption
is carried into the output artifact and labelled a stated assumption (FR-051), so a reader cannot
mistake a projection for an observation.

**Alternatives considered**: fitting a macro-conditional model with observed macro series joined in —
more principled, but requires an external data source with its own provenance and terms obligations,
and the problem statement supplies scenario assumptions rather than macro history; Monte Carlo over
assumption distributions — a genuine improvement, deferred, because point projections under three
named scenarios are what the criterion asks for.

---

## 14. Next-state definition

**Decision**: `next_state` is the loan's state at `m + 3`, over the state set
`{current, dq_30, dq_60, dq_90_plus, prepaid, defaulted}` derived from delinquency status and
zero-balance code. States with no observed instances in a split are reported as **undefined** rather
than as zero performance (SC-011).

**Rationale**: a three-month horizon matches the near-term deterioration outcome so the two are
mutually consistent, and the state set collapses the long delinquency tail (`04`–`99`) into one bucket
because the measured counts thin out sharply beyond three months delinquent — reporting per-state
metrics on cells with single-digit support would be noise presented as measurement.

**Open dependency**: if the problem statement enumerates an explicit state vocabulary, that vocabulary
supersedes this one and the mapping moves into `config/field_mapping.yaml`. Recorded as a config
change, not a code change.

---

## Resolved: no NEEDS CLARIFICATION items remain

Fourteen decisions, each with a named rejected alternative. Three are flagged as reversible on
evidence rather than settled: level-2 positive-keeping (§2), discrete-time multinomial hazard as a
fallback for Cox (§8), and the next-state vocabulary pending confirmation against the problem
statement (§14).
