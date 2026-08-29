# Feature Specification: Loan Performance Intelligence Engine

**Feature Branch**: `001-loan-performance-intelligence`

**Created**: 2026-08-27

**Status**: Draft

**Input**: Intain Campus FinTech Challenge 2026 — AI Track Problem Statement, "Loan Performance
Intelligence Engine". Build an ML-first system for loan-data profiling, performance prediction,
anomaly detection, scenario simulation, explainability, and grounded LLM-assisted review.

**Governing document**: [`.specify/memory/constitution.md`](../../.specify/memory/constitution.md)
v1.0.0. Principles I (ML-First — The LLM Never Decides) and II (Leakage Containment) are
non-negotiable and cannot be traded away for scope.

**Data ground truth**: [`docs/data-provenance.md`](../../docs/data-provenance.md). All volumes and
rates cited in this spec were measured by full scan, not estimated.

---

## Testing Requirement *(explicit — do not treat as optional)*

**Tests are MANDATORY for this feature.** The tasks template treats tests as conditional on the
specification requesting them; this section is that request. The suite MUST include at minimum the
six enforcement tests named in FR-069 through FR-074. A deliverable that lacks them is not
complete regardless of how well it scores on other criteria, because Principles I and II are
enforced by test rather than by convention.

---

## User Scenarios & Testing *(mandatory)*

Stories are ordered so that a submittable artifact exists after US1 and every later story
strictly increases judged value without risking the submission. Each story names the judging
criterion and point value it primarily serves, so effort can be allocated against the rubric.

### User Story 1 - A Complete, Submittable Baseline (Priority: P1) 🎯 MVP

**Serves**: a thin slice of every criterion. Establishes the 13 items of the Minimum Acceptable
Solution and nothing beyond them.

A reviewer points the engine at raw loan data and receives, in one run: a data-quality profile, a
set of loan-month predictions for deterioration and prepayment, an anomaly score per record, a
plain-language explanation of what drove each score, a reviewer note summarising the case, and a
correctly formatted submission file. Nothing in this run is state of the art; everything in it is
complete, honest, and reproducible.

**Why this priority**: The single largest project risk is finishing with sophisticated components
and no valid submission. Nine of the ten §13 disqualification conditions can be triggered by
process failure rather than modelling weakness. This story makes the submission exist first, so
every later story is an improvement on something rather than a bet on something.

**Independent Test**: From a clean checkout with raw data present, one documented command
completes and produces a submission file that passes schema validation, plus a profiling report,
a metrics file, an explanation artifact, a reviewer note, and a model card. Re-running the command
produces byte-identical output. Disabling the language model still produces a valid submission.

**Acceptance Scenarios**:

1. **Given** raw loan files and no prior run artifacts, **When** the reviewer runs the pipeline
   command, **Then** the run completes without manual intervention and every declared artifact
   exists on disk.
2. **Given** a completed run, **When** the submission file is validated against the required
   column contract, **Then** column names, order, types, value domains, and row count all pass
   and no required field contains nulls.
3. **Given** a completed run, **When** the run is repeated with the same configuration and seed,
   **Then** the submission file is byte-identical to the first run.
4. **Given** a completed run, **When** any metric is quoted in a report, **Then** that number is
   present in a machine-readable metrics artifact written by the same run.
5. **Given** the language-model provider is disabled or unconfigured, **When** the pipeline runs,
   **Then** it completes successfully and reviewer notes are produced deterministically instead of
   failing.
6. **Given** a trained model, **When** the feature matrix is inspected, **Then** it contains no
   outcome column and no column derived from an outcome column.

---

### User Story 2 - Trustworthy Data Before Any Model (Priority: P2)

**Serves**: Data Intelligence and Profiling — **15 points**.

A data steward needs to know what is wrong with the data before believing anything predicted from
it. They receive per-column distributions, missingness patterns rather than just missingness
counts, outliers, invalid date relationships, cross-column contradictions, correlation and
dependency structure, a comparison of how the scoring population differs from the training
population, and a defensible quality score at both the record and batch level.

**Why this priority**: The constitution requires profiling to precede feature engineering, so this
work gates the highest-value modelling story. It is also the second-largest single criterion, and
the measured data contains genuine defects to find — 31.4% of loans never terminate, sentinel
values such as `9999` for credit score and `999` for debt-to-income masquerade as real numbers,
and the recent vintages sit in a visibly different regime from the crisis vintages.

**Independent Test**: Run profiling alone against raw data with no model present. The report
identifies the known sentinel-value columns, quantifies missingness patterns, flags records
violating at least one documented cross-column rule, and reports a population-shift measure per
feature between the training and scoring windows with a ranked list of the most shifted fields.

**Acceptance Scenarios**:

1. **Given** raw data containing sentinel values that are numerically valid but semantically
   missing, **When** profiling runs, **Then** those values are reported as disguised missingness
   and not as legitimate extremes.
2. **Given** records where a maturity date precedes an origination date or a balance rises without
   a modification, **When** profiling runs, **Then** each violated rule is reported with the count
   and a sample of offending record identifiers.
3. **Given** a training window and a later scoring window, **When** drift analysis runs, **Then**
   each feature receives a shift magnitude and the fields most responsible for population change
   are ranked.
4. **Given** any record, **When** quality scoring runs, **Then** the record receives a score whose
   components are individually inspectable rather than an opaque single number.
5. **Given** a batch of records, **When** batch scoring runs, **Then** the batch score is
   reproducible and its derivation from record scores is documented.

---

### User Story 3 - Multi-Outcome Prediction That Survives Scrutiny (Priority: P2)

**Serves**: Predictive Modeling — **20 points**, the largest single criterion.

A risk analyst needs calibrated probabilities for several distinct futures — near-term
delinquency, longer-horizon delinquency, default, prepayment — plus the loan's most likely next
state. They need to see that a simple baseline was beaten by a considered model, that the severe
class imbalance was handled deliberately, and that predicted probabilities mean what they claim
when compared against observed frequencies.

**Why this priority**: Highest point value, and the criterion where §13's leakage conditions are
most easily triggered. The measured 96.34% current rate means a model can appear excellent while
being useless, so this story is as much about honest measurement as about model quality.

**Independent Test**: Train on an early time window, evaluate on a strictly later window, and
report discrimination and calibration for each outcome alongside the positive base rate. A named
baseline and a named improved model are both reported on identical splits, and a reliability
comparison shows whether calibration improved.

**Acceptance Scenarios**:

1. **Given** a panel spanning many reporting months, **When** splits are created, **Then** the
   training, validation, and scoring windows occupy disjoint and ordered month ranges, and this is
   recorded in an audit artifact.
2. **Given** a single loan observed across many months, **When** splits are created, **Then** no
   loan-month row is assigned to an earlier split than a row of the same loan in a later month.
3. **Given** an outcome with a positive rate far below 50%, **When** results are reported,
   **Then** precision-recall performance, recall at a fixed precision, and a probability-accuracy
   score are reported together with the positive base rate, and headline accuracy is not presented
   as evidence of quality.
4. **Given** a baseline model and an improved model, **When** both are evaluated, **Then** they are
   compared on identical splits and the comparison states which outcomes improved and which did
   not.
5. **Given** predicted probabilities, **When** calibration is assessed, **Then** predicted versus
   observed frequency is reported across probability bands and any systematic over- or
   under-prediction is stated plainly.
6. **Given** a next-state prediction task, **When** results are reported, **Then** performance is
   reported per state as well as in aggregate, so rare states are not hidden by common ones.

---

### User Story 4 - Time-to-Event With Competing Risks (Priority: P3)

**Serves**: Time-to-Event / Transition Modeling — **15 points**.

An analyst asks not merely *whether* a loan will deteriorate but *when*, and needs the answer to
respect the fact that a loan which pays off early can no longer default. They receive cumulative
event probabilities over loan age, an explicit account of how incomplete observation was handled,
and a comparison against a simpler approach.

**Why this priority**: Third-largest criterion, and the measured data supports it unusually well —
31.4% of loans are genuinely right-censored and prepayment at roughly 64% of loans directly
competes with credit events at roughly 2.9%. Treating default in isolation would overstate default
risk, which is a specification error rather than a tuning choice.

**Independent Test**: Fit a time-to-event model on loans with known origination timing, produce
cumulative incidence curves for at least two competing outcomes, demonstrate that censored loans
contribute to the risk set only while observed, and compare discriminative performance against a
simpler baseline on the same population.

**Acceptance Scenarios**:

1. **Given** loans still active at the end of observation, **When** the model is fitted, **Then**
   those loans are treated as censored at their last observed month rather than as non-events.
2. **Given** two outcomes that compete for the same loan, **When** cumulative incidence is
   reported, **Then** the curves account for the competing outcome and their sum does not exceed
   one.
3. **Given** a fitted model, **When** curves are presented, **Then** they are shown against loan
   age and are accompanied by the number of loans still at risk at each horizon.
4. **Given** a simpler alternative approach, **When** both are evaluated, **Then** a like-for-like
   comparison is reported and the reason for preferring one is stated.
5. **Given** any transition-style formulation, **When** it is used, **Then** the state space and
   the treatment of absorbing states are documented.

---

### User Story 5 - A Reviewer Queue Worth a Reviewer's Time (Priority: P3)

**Serves**: Anomaly and Exception Intelligence — **10 points**.

A reviewer opens a prioritised queue of suspicious records. Each entry carries an anomaly score, a
predicted probability that an exception is genuinely required, a predicted exception category, and
the specific reasons it was flagged. Deterministic rule violations and learned statistical
oddities are both represented and distinguishable.

**Why this priority**: Directly required by §8 Task 4 including a minimum of twenty
reviewer-ready examples, and it is the story that makes the system feel operational rather than
academic. It depends on profiling (US2) for its rule layer.

**Independent Test**: Produce a ranked queue from scored data containing at least twenty examples,
each with a score, an exception category, and named contributing drivers. Verify that a record
violating a deterministic rule and a record that is merely statistically unusual are both present
and separately attributable.

**Acceptance Scenarios**:

1. **Given** a scored population, **When** the queue is produced, **Then** it contains at least
   twenty entries ordered by a documented priority and each entry names its contributing drivers.
2. **Given** a record that violates a deterministic validation rule, **When** it is flagged,
   **Then** the specific rule is identified by name rather than only by score.
3. **Given** a record that violates no rule but is statistically unusual, **When** it is flagged,
   **Then** the fields responsible for its unusualness are named.
4. **Given** an exception category prediction, **When** it is reported, **Then** it is accompanied
   by a confidence measure and the category vocabulary is documented.
5. **Given** the reconciliation fixture representing a conflicting second source, **When** it is
   used, **Then** every artifact and report that references it labels it as constructed rather
   than observed.

---

### User Story 6 - Scenario and Stress Projection (Priority: P4)

**Serves**: Scenario and Stress Simulation — **10 points**.

A risk manager selects a scenario — baseline, adverse credit, or elevated prepayment — and sees
projected deterioration, default, and prepayment rates for the portfolio, broken out by vintage,
credit band, geography, and servicer, with the drivers of the change from baseline made explicit.

**Why this priority**: Fully required by §8 Task 5 and cheap once calibrated models exist, but it
depends on US3 and is worthless without it — projecting from an uncalibrated model produces
confident nonsense.

**Independent Test**: Apply all three scenarios to the same population and confirm the projections
differ in the expected direction, that segment breakdowns sum consistently to portfolio totals,
and that the largest contributors to each scenario's change from baseline are identified.

**Acceptance Scenarios**:

1. **Given** three scenario definitions, **When** projections are produced, **Then** each yields
   deterioration, default, and prepayment rates, and the adverse scenario shows higher credit
   stress than baseline while the prepayment scenario shows higher prepayment.
2. **Given** segment definitions, **When** projections are broken out, **Then** segment results
   reconcile with the portfolio total within a documented tolerance.
3. **Given** a scenario projection, **When** drivers are reported, **Then** the assumptions and
   segments contributing most to the change from baseline are ranked.
4. **Given** scenario assumptions, **When** they are presented, **Then** they are labelled as
   stated assumptions rather than as observed or forecast data.

---

### User Story 7 - Explanations and Declared Limits (Priority: P4)

**Serves**: Explainability and Responsible AI — **10 points**.

A reviewer or validator needs to know why the system said what it said, both across the portfolio
and for one specific loan, together with how confident the system is, where it fails, and what it
cannot do. They receive global importance, local per-loan attribution, uncertainty, concrete
false-positive and false-negative cases, and a model card that states limitations without
euphemism.

**Why this priority**: §13 disqualifies a solution that "cannot explain model behavior", and US1
already delivers a minimal explanation. This story raises minimal to defensible.

**Independent Test**: For a chosen loan, produce a local attribution whose top drivers are
consistent with the global importance ranking's treatment of those features, alongside a
confidence measure. Separately produce curated false positives and false negatives with commentary
on what the model got wrong and why.

**Acceptance Scenarios**:

1. **Given** a fitted model, **When** global importance is reported, **Then** it is accompanied by
   the method used and its known limitations.
2. **Given** one loan-month record, **When** a local explanation is requested, **Then** the
   contribution of individual features to that specific prediction is reported and the
   contributions reconcile with the prediction within a documented tolerance.
3. **Given** any prediction, **When** confidence is reported, **Then** the meaning of the
   confidence measure is documented and it is not presented as a probability of correctness unless
   it is one.
4. **Given** evaluation results, **When** error analysis is reported, **Then** concrete
   false-positive and false-negative records are shown with their drivers.
5. **Given** the completed system, **When** the model card is produced, **Then** it states
   objective, data, features, model type, validation method, metrics, leakage controls,
   limitations, and known failure modes, and every metric in it is read from a run artifact.

---

### User Story 8 - A Copilot That Recommends and Never Decides (Priority: P5)

**Serves**: Smart LLM Usage — **10 points**.

A reviewer reads a natural-language case summary that explains a flagged loan in plain terms,
quotes the relevant field definitions, and proposes an action — clearly marked as a recommendation
requiring human confirmation. Every generated word is traceable to model output or retrieved
reference material, every call is logged, and cases where the assistant was wrong are preserved
rather than hidden.

**Why this priority**: US1 already satisfies the minimum requirement for a reviewer summary, so
this is depth rather than existence. It is deliberately last because §13 disqualifies
over-reliance on generated text, making this the story where adding more carries the most risk if
the grounding controls are not already solid.

**Independent Test**: Generate a note for a flagged loan, confirm every factual claim traces to
supplied context, confirm the call appears in the prompt log with its full inputs and outputs, and
confirm a deliberately fabricated numeric claim is caught and rejected by the validator rather
than surfaced to the reviewer.

**Acceptance Scenarios**:

1. **Given** a flagged loan and its model outputs, **When** a reviewer note is generated, **Then**
   every numeric claim in the note matches a value supplied in the grounding context.
2. **Given** a generated note containing a value absent from the grounding context, **When**
   validation runs, **Then** the note is rejected, the rejection is logged with its reason, and no
   unvalidated text reaches the reviewer.
3. **Given** any generation, **When** the prompt log is inspected, **Then** it contains timestamp,
   provider, model identifier, full prompt, full response, and the accept-or-reject outcome.
4. **Given** a generated recommendation, **When** it is presented, **Then** it is explicitly
   labelled a recommendation and the reviewer action remains a human or rule-based output.
5. **Given** a request for a field definition, **When** the assistant answers, **Then** the answer
   quotes the reference material rather than paraphrasing from memory.
6. **Given** the development history, **When** rejected outputs are reviewed, **Then** concrete
   preserved examples exist of the assistant being wrong, vague, or overconfident, each annotated
   with what failed and how it was detected.

---

### Edge Cases

- **Sentinel values that are valid numbers**: credit score `9999`, debt-to-income `999`,
  loan-to-value `999`, borrower count `99`. Treated as real values these silently poison every
  distribution and model. They must be recognised as disguised missingness.
- **Loans that never terminate**: 94,185 of 300,000. Treating them as non-events biases every
  time-to-event estimate downward.
- **Negative remaining term**: observed as low as −8 months, meaning loans persisting past legal
  maturity. Must not be discarded silently or clipped without record.
- **Balance increasing month over month**: legitimate under capitalising modification, a defect
  otherwise. The rule must be conditional rather than absolute.
- **Loans terminating in the first observed month**: no history exists from which to build lagged
  features.
- **Administrative terminations that look like outcomes**: 3,572 loans leave the population through
  a securitization or a confirmed origination defect rather than through payoff or loss. Their loss
  fields are zeroed by design, so counting them as defaults would overstate credit events by 39%
  while counting them as payoffs would understate them. They must be removed from the label
  population, not bucketed.
- **A termination code that changed meaning between dataset releases**: one loan-sale code was
  split by the publisher in 2023, and code written against the older definition silently
  understates defaults. Coded-value handling must be pinned to the release actually on disk.
- **Vintage regime shift**: crisis-era and pandemic-era loss mitigation differ structurally
  (472,662 payment-deferral records, 49,568 forbearance records). A model trained across both
  without regime awareness may learn an average that describes neither.
- **Scoring population containing loans unseen in training**: expected and correct under a
  time-aware split; must not error.
- **Categorical levels present only in the scoring window**: for example a servicer that appears
  late. Must not error.
- **Language model unavailable, rate-limited, or returning malformed output**: must degrade, never
  fail the run.
- **Empty reviewer queue**: if nothing is anomalous, the system must say so rather than pad the
  queue to reach twenty entries.
- **Extreme class scarcity within a segment**: a segment may contain zero positives, making
  segment-level metrics undefined. Must report as undefined rather than as zero.
- **Loss amounts whose sign convention inverted between dataset releases**: recoveries and proceeds
  are negative in the release on disk and positive in earlier ones, so the publisher's own published
  loss formula no longer evaluates correctly. Any derived loss quantity must be validated against
  the pre-computed field rather than recomputed from components on trust.
- **Loan age that resets mid-life**: age restarts at modification but not at payment deferral, so it
  is not a clean seasoning variable for the 8,391 modified loans. Using it as one would attribute
  modification effects to youth.
- **A field that is a count in one file and a missingness sentinel in another**: `99` means
  ninety-nine months delinquent in the monthly file but "not available" in three origination fields.
  A single global sentinel list would corrupt the delinquency label itself.

---

## Requirements *(mandatory)*

### Functional Requirements

#### Data ingestion and contract

- **FR-001**: The system MUST read the raw loan-level source files without requiring manual
  pre-editing, given their documented layout of one origination record per loan and one
  performance record per loan per reporting month.
- **FR-002**: The system MUST translate source field names into the problem statement's field
  vocabulary through declarative configuration, so that substituting a differently-named but
  semantically equivalent dataset requires no change to processing logic.
- **FR-003**: The system MUST reject or quarantine records that fail structural validation, and
  MUST report the count and reason rather than dropping them silently.
- **FR-004**: The system MUST recognise documented sentinel values as missing rather than as
  numeric extremes, and MUST record which values were reinterpreted for which fields.
- **FR-005**: The system MUST decode coded categorical fields into documented human-readable
  meanings, and MUST fail loudly on an unrecognised code rather than silently passing it through.
- **FR-006**: The system MUST reduce the source volume to a working population by sampling at the
  whole-loan level so that no loan appears partially, and MUST record the sampling rule, the seed,
  and the resulting loan and row counts.
- **FR-007**: The system MUST produce the problem statement's expected data-pack files, and MUST
  label every file it constructs rather than derives from source as constructed, in both the file
  documentation and the model card.
- **FR-008**: The system MUST author a field-definition reference covering every field used, in a
  form suitable both for human reading and for retrieval as grounding material.
- **FR-009**: The system MUST express deterministic data-quality checks as external configuration
  rather than embedded logic, so rules can be added without code change.

#### Profiling and data intelligence

- **FR-010**: The system MUST report, per field, the distribution summary appropriate to its type,
  the missing rate, and the distinct-value count.
- **FR-011**: The system MUST report missingness as co-occurring patterns across fields, not only
  as independent per-field rates.
- **FR-012**: The system MUST detect and report outliers by a documented method, and MUST
  distinguish statistical outliers from rule violations.
- **FR-013**: The system MUST validate relationships between dates and report every violation,
  including maturity preceding origination and reporting months outside a loan's observable life.
- **FR-014**: The system MUST report pairwise association among fields and identify near-duplicate
  or highly dependent fields.
- **FR-015**: The system MUST detect cross-field contradictions where one field's value is
  impossible given another's.
- **FR-016**: The system MUST quantify population shift between the training window and the
  scoring window per field, and MUST rank fields by shift magnitude.
- **FR-017**: The system MUST assign every record a quality score whose contributing components
  are individually reported.
- **FR-018**: The system MUST assign every batch a quality score with a documented derivation from
  record scores.
- **FR-019**: The system MUST emit profiling output as a durable artifact readable independently of
  any interactive interface.

#### Feature construction

- **FR-020**: The system MUST construct features through a single shared transformation layer;
  ad-hoc feature computation outside that layer is prohibited.
- **FR-021**: The system MUST compute every historical feature using only records at or before the
  record's as-of month, grouped by loan.
- **FR-022**: The system MUST fit all preprocessing statistics on training data only and apply
  them unchanged to later windows.
- **FR-023**: The system MUST handle categorical levels unseen at training time without error.
- **FR-024**: The system MUST record the exact feature list used by each model as an artifact.

#### Outcome definition

- **FR-025**: The system MUST define each predicted outcome as an explicit, documented function of
  future observed records, stating the horizon and the condition that constitutes the event.
- **FR-026**: The system MUST document its classification of every termination reason as voluntary
  payoff, credit event, or administrative removal, MUST cite the evidence for each classification,
  and MUST report the resulting event rates.
- **FR-027**: The system MUST exclude administrative-removal terminations from the label population
  rather than classifying them as either payoff or credit event, MUST report the count excluded, and
  MUST corroborate each credit-event classification against an independent field that is populated
  only for genuine credit events.
- **FR-028**: The system MUST exclude from an outcome's training population any record whose
  outcome cannot be determined because the observation window ends before the horizon closes, and
  MUST report how many records this removes.

#### Prediction

- **FR-029**: Every predicted quantity delivered to a consumer MUST originate from a model fitted
  on data. No predicted value may be produced by generated text.
- **FR-030**: The system MUST predict near-term deterioration, longer-horizon deterioration,
  default, and voluntary payoff, and MUST predict the most likely next state.
- **FR-031**: The system MUST separate data into training, validation, and scoring windows by
  reporting month such that the windows are disjoint and ordered; random assignment of rows is
  prohibited.
- **FR-032**: The system MUST report a named simple baseline and a named improved model for each
  outcome, evaluated on identical splits.
- **FR-033**: The system MUST apply a documented technique for class imbalance and MUST report the
  positive base rate alongside every performance figure.
- **FR-034**: The system MUST report precision-recall performance, ranking performance, recall at a
  documented fixed precision, and a probability-accuracy score for each binary outcome, and
  per-class as well as averaged performance for the multi-state outcome.
- **FR-035**: The system MUST calibrate predicted probabilities and MUST report predicted versus
  observed frequency across probability bands both before and after calibration.
- **FR-036**: The system MUST NOT present headline accuracy as primary evidence of quality for any
  outcome whose positive rate is below one third.

#### Time to event

- **FR-037**: The system MUST estimate time to event using a method that accounts for incomplete
  observation, and MUST document how censoring is determined.
- **FR-038**: The system MUST produce cumulative event probabilities over loan age for at least
  two outcomes that compete for the same loan.
- **FR-039**: The system MUST account for the competing outcome when estimating each outcome's
  cumulative incidence, such that the estimates are not each computed as though the other could
  not occur.
- **FR-040**: The system MUST report the population still at risk at each reported horizon.
- **FR-041**: The system MUST compare its time-to-event model against a simpler alternative on the
  same population and state the basis for preferring one.

#### Anomaly and exception

- **FR-042**: The system MUST assign every record an anomaly score by a documented method.
- **FR-043**: The system MUST predict whether an exception is required and, when it is, which
  category applies, with a documented category vocabulary.
- **FR-044**: The system MUST name the fields or rules responsible for each flagged record.
- **FR-045**: The system MUST combine deterministic rule violations with learned statistical
  detection and MUST make the two distinguishable in output.
- **FR-046**: The system MUST produce a prioritised reviewer queue of at least twenty entries when
  at least twenty records warrant review, and MUST state plainly when fewer do.

#### Scenario

- **FR-047**: The system MUST accept scenario assumptions as external configuration.
- **FR-048**: The system MUST project deterioration, default, and payoff rates under a baseline, an
  adverse-credit, and an elevated-payoff scenario.
- **FR-049**: The system MUST report projections broken out by vintage, credit band, geography, and
  servicer.
- **FR-050**: The system MUST rank the assumptions and segments contributing most to each
  scenario's divergence from baseline.
- **FR-051**: The system MUST label scenario assumptions as stated assumptions wherever they
  appear.

#### Explainability

- **FR-052**: The system MUST report global feature importance with the method named and its
  limitations stated.
- **FR-053**: The system MUST produce a local attribution for any individual record on request.
- **FR-054**: The system MUST report a confidence or uncertainty measure with each prediction and
  MUST document what that measure does and does not mean.
- **FR-055**: The system MUST report concrete false-positive and false-negative examples with their
  drivers.
- **FR-056**: The system MUST generate a model card containing objective, data, features, model
  type, validation method, metrics, leakage controls, limitations, and known failure modes.

#### Assisted review

- **FR-057**: The system MUST generate reviewer-facing natural-language summaries grounded
  exclusively in supplied model output and retrieved reference material.
- **FR-058**: The system MUST log every generation with timestamp, provider, model identifier, full
  prompt, full response, and accept-or-reject outcome, in an append-only record.
- **FR-059**: The system MUST validate generated text against its grounding context, MUST reject
  text containing unsupported factual or numeric claims, and MUST retain rejections with reasons.
- **FR-060**: The system MUST label every generated artifact as a recommendation and MUST NOT
  permit generated text to determine a reviewer action or any submitted value.
- **FR-061**: The system MUST remain fully functional with no generation provider configured,
  substituting deterministic summaries.
- **FR-062**: The system MUST maintain a curated collection of generation failures — wrong, vague,
  or overconfident outputs — annotated with what failed and how it was detected.

#### Reproducibility, delivery, and enforcement

- **FR-063**: The system MUST complete the entire flow from raw source data to every deliverable
  through one documented command.
- **FR-064**: The system MUST derive all randomness from a single configured seed and MUST produce
  identical output across runs with identical configuration.
- **FR-065**: The system MUST emit each required deliverable as a build output written by code, not
  assembled by hand.
- **FR-066**: The system MUST validate the submission file against its required column contract and
  MUST fail the run when validation fails.
- **FR-067**: The system MUST maintain a development log recording tools used, representative
  prompts, accepted and rejected outputs, the human review process, and the approximate share of
  generated code, updated as work proceeds rather than reconstructed afterwards.
- **FR-068**: The system MUST provide an interactive demonstration surface that reads only
  artifacts produced by the command-line flow, so that the demonstration and the documents cannot
  disagree.
- **FR-069**: The system MUST include an automated check that no outcome column and no
  outcome-derived column reaches a fitted model.
- **FR-070**: The system MUST include an automated check that split windows are disjoint and
  ordered in time.
- **FR-071**: The system MUST include an automated check that two runs with identical configuration
  produce identical submission output.
- **FR-072**: The system MUST include an automated check that the submission file satisfies its
  column contract.
- **FR-073**: The system MUST include an automated check that the full flow succeeds with the
  generation provider disabled.
- **FR-074**: The system MUST include an automated check that a fabricated numeric claim in
  generated text is rejected by the grounding validator.

### Key Entities

- **Loan**: one borrowing arrangement, identified by a stable identifier, with fixed attributes
  established at origination and a life history of monthly records.
- **Loan-Month Record**: the state of one loan in one reporting month — balance, rate, payment
  status, months delinquent, modification and assistance status, remaining term, and the servicer
  reporting it. The unit of prediction.
- **Static Attributes**: characteristics fixed at origination — original balance, rate, term,
  credit band, loan-to-value band, debt-to-income band, geography, purpose, occupancy, property
  type, vintage, seller.
- **Outcome**: a labelled future condition of a loan derived from records after an as-of month,
  each with an explicit horizon and event definition.
- **Termination Event**: the reason a loan left the population, classified as voluntary payoff,
  credit event, or neither, with the classification and its ambiguity documented.
- **Split Definition**: the month boundaries partitioning the panel into training, validation, and
  scoring windows, together with resulting counts — an auditable artifact, not an implicit choice.
- **Feature Set**: the named, ordered inputs to a model, with the as-of rule under which each was
  computed.
- **Validation Rule**: a named deterministic condition a record must satisfy, with a severity and a
  human-readable description.
- **Quality Score**: a composite record- or batch-level assessment with individually inspectable
  components.
- **Anomaly Finding**: a flagged record with a score, the responsible fields or rules, a predicted
  exception category, and a confidence.
- **Scenario**: a named set of stated assumptions about future conditions, and the projections
  produced under it.
- **Explanation**: global or record-level attribution of a prediction to its inputs, with the
  method and its limitations named.
- **Generation Record**: one assisted-review interaction — timestamp, provider, model, prompt,
  response, grounding context, validation outcome, and accept-or-reject decision.
- **Reviewer Note**: a validated natural-language summary explicitly marked as a recommendation.
- **Submission Row**: the required per-record output — probabilities, next state, exception
  category, anomaly score, top drivers, action, and confidence.
- **Model Card**: the governing description of a model's purpose, construction, validation,
  measured performance, and declared limits.

---

## Success Criteria *(mandatory)*

Criteria are stated as verifiable outcomes. Absolute performance thresholds are deliberately
avoided where no honest target can be set in advance; Principle V forbids committing to a number
before measuring it. Where a floor is given, it is one that a non-functional model genuinely
cannot clear.

### Measurable Outcomes

#### Correctness and integrity

- **SC-001**: A clean checkout with source data present produces every declared deliverable
  through one command, with no manual step, on at least two consecutive attempts.
- **SC-002**: Two runs with identical configuration produce byte-identical submission output.
- **SC-003**: The submission file passes its full column contract with zero violations.
- **SC-004**: No outcome column or outcome-derived column appears in any model's recorded feature
  list — verified automatically, not by inspection.
- **SC-005**: Training, validation, and scoring month ranges are disjoint and ordered, evidenced by
  a run-produced audit artifact reporting boundary overlap counts of zero.
- **SC-006**: The complete flow succeeds with the generation provider disabled, producing a valid
  submission.
- **SC-007**: Every number appearing in any report or documentation is locatable in a
  machine-readable artifact produced by the run that reported it.

#### Predictive value

- **SC-008**: For every binary outcome, the improved model's precision-recall performance exceeds
  the outcome's positive base rate on a strictly later scoring window — the floor a
  non-informative model cannot pass.
- **SC-009**: For every outcome, a named baseline and a named improved model are reported on
  identical splits, with improvements and regressions both stated.
- **SC-010**: Calibration is reported before and after adjustment for every outcome, and the
  direction of any residual systematic bias is stated.
- **SC-011**: Multi-state prediction reports per-state performance, with states having no observed
  instances reported as undefined rather than as zero.
- **SC-012**: Cumulative incidence estimates for competing outcomes sum to no more than one at
  every reported horizon.
- **SC-013**: The time-to-event model is compared against a simpler alternative on the same
  population, with the preference justified.

#### Operational usefulness

- **SC-014**: Profiling identifies every documented sentinel-value field as disguised missingness,
  with none missed.
- **SC-015**: Population shift is quantified for every field and the most shifted fields are
  ranked.
- **SC-016**: Every record receives a quality score whose components are individually reportable.
- **SC-017**: The reviewer queue presents at least twenty entries, each naming its contributing
  drivers, with rule-based and statistical flags distinguishable.
- **SC-018**: All three scenarios produce projections that differ from one another in the
  documented expected direction, with segment results reconciling to portfolio totals within a
  stated tolerance.
- **SC-019**: A local explanation can be produced for any individual record, with contributions
  reconciling to the prediction within a stated tolerance.

#### Governance

- **SC-020**: Every generation is present in the prompt log with all required fields populated.
- **SC-021**: A deliberately fabricated numeric claim inserted into generated text is rejected by
  the grounding validator and never reaches a reviewer-facing artifact.
- **SC-022**: At least one curated, annotated example exists of the assistant being wrong, vague,
  or overconfident.
- **SC-023**: Every generated artifact carries a recommendation label, and no submitted value
  originates from generated text.
- **SC-024**: The model card states limitations and known failure modes, with every metric traced
  to a run artifact.
- **SC-025**: The development log covers tools, prompts, accepted and rejected outputs, review
  process, and generated-code share, with evidence of incremental rather than retrospective
  authorship.
- **SC-026**: Every constructed data file is labelled as constructed in its documentation and in
  the model card.

---

## Out of Scope

Named explicitly so that scope is bounded rather than merely unstated. Anything here is a deliberate
exclusion, not an oversight.

- **Loss severity and dollar-loss modelling.** The system predicts whether and when events occur,
  not how much is lost. The source data carries loss fields, but the problem statement asks for
  event prediction, and the release on disk inverted the sign convention on those fields — modelling
  them would add risk without adding judged value.
- **Macroeconomic forecasting.** Scenario inputs are stated stress assumptions. No interest-rate,
  unemployment, or house-price forecast is produced or claimed.
- **Real-time or streaming scoring.** Scoring is batch, run on demand.
- **Distributed or GPU compute.** Single machine, in-memory working population.
- **A writable interactive interface.** The interactive surface reads run artifacts only. It cannot
  trigger training, alter configuration, or write results, so it can never disagree with the
  documents.
- **Authentication, multi-tenancy, and access control.** Single-analyst local tool.
- **Automated action on any prediction.** Every recommendation terminates at a human. No downstream
  system is triggered.
- **Full-population processing.** The full published dataset is roughly 100 GB; the sample subset is
  used, and even that is sampled down. Absolute portfolio figures are therefore representative of
  the sample, not of the publisher's book, and are labelled as such.
- **Adjustable-rate and interest-only products.** Absent from the source subset entirely — every
  loan is fixed-rate and fully amortizing. No claim is made about products the data does not
  contain.
- **Fairness analysis on protected attributes.** The source data contains no race, ethnicity, sex,
  or age fields, so direct fairness testing is impossible. Geographic and credit-band disparity
  reporting is in scope as a proxy-level substitute, and the absence of protected attributes is
  stated as a declared limitation rather than presented as a clean bill of health.

## Assumptions

Each assumption below is a decision made in the absence of an explicit instruction, recorded so it
can be challenged rather than discovered later.

1. **Termination-code meanings are verified, not assumed.** The mapping from termination code to
   voluntary payoff versus credit event was confirmed against the source publisher's official
   release notes and user guide, and then independently corroborated twice: the loss fields are
   populated only for genuine credit events, and delinquency status at termination is current for
   98.9% of payoffs but deeply delinquent for credit events. This is recorded here because an
   earlier draft treated it as a provisional assumption; it is now a measured fact. See
   [`docs/freddie-mac-r47-layout.md`](../../docs/freddie-mac-r47-layout.md).
2. **Loan-sale termination codes are not ambiguous, and are split.** An earlier draft assumed the
   two loan-sale codes were jointly ambiguous and defaulted both to censored. That was wrong. The
   publisher split them in a 2023 release: one retained non-performing (note) sales **with losses
   disclosed** and is therefore a credit event; the other took reperforming securitizations **with
   no losses** and is an administrative removal. A third code covers confirmed origination defects,
   whose loss fields are zeroed by design; those are repurchases, not zero-loss defaults, and are
   also removed. Removing rather than mislabelling these 3,572 loans is a correctness requirement,
   not a modelling preference — counting them as defaults would overstate credit events by 39%, and
   counting them as payoffs would understate them.
3. **The scoring set is constructed by time-aware holdout.** The problem statement anticipates an
   organiser-supplied unlabelled scoring file. None exists, so the latest reporting months are held
   out and their labels withheld. If an official scoring file arrives it supersedes this, as a
   configuration change.
4. **Submission granularity is one row per scored loan-month.** The problem statement describes
   per-record submission of probabilities, anomaly scores, and reviewer actions without stating the
   unit. The prediction unit is used, which is the reading most consistent with its field list.
5. **The working population is sampled to the volume band the problem statement suggests.** The
   available 19,248,196 rows exceed the suggested 250,000 to 1,000,000. Sampling is performed at
   whole-loan level to preserve complete loan histories, with the rule and seed recorded.
6. **All six vintages are retained in the working population.** Discarding crisis vintages would
   remove most credit events; discarding recent vintages would remove the genuine regime shift that
   makes drift analysis meaningful.
7. **The conflicting-second-source file is a constructed fixture.** The source data carries one
   authoritative record per loan-month, so genuine cross-source conflict does not exist within it.
   Reconciliation logic is therefore exercised against a constructed fixture, labelled as such
   everywhere it appears. Presenting it as observed data would be a reporting violation. Servicer
   *transfers*, by contrast, are real and time-varying, so any servicer-based segmentation is
   treated as as-of-month rather than as a static loan attribute.
8. **Scenario assumptions are stated, not forecast.** No macroeconomic forecast is claimed. Scenario
   inputs are illustrative stress assumptions and are labelled as such.
9. **Only three origination fields are excluded as information-free.** An earlier draft excluded
   seven, based on a measurement taken on one vintage and generalised — an error. Pooled across all
   six vintages only three fields are genuinely constant. The other four carry real signal,
   including two that identify a structurally distinct refinance population, and are retained. Any
   future exclusion decision must be measured across the full working population, not a single
   vintage.
10. **Sentinel values are dataset conventions.** Values such as a credit score of `9999` and a
    debt-to-income of `999` are read as missingness markers rather than extreme observations, per
    the source's documented conventions. One exception is explicit: in the monthly delinquency
    status field, `99` is a genuine count of months delinquent and must not be treated as missing.
11. **A single machine, offline after data acquisition.** No distributed compute is assumed. The
    working population must therefore fit comfortably in memory on one machine, which further
    motivates sampling.
12. **Judges will read documents and may run the code.** Deliverables are written to stand alone
    without narration, and the command-line flow is the authoritative interface rather than the
    interactive one.
13. **Two source field names rest on inference.** The publisher has not released a layout document
    for the release our files belong to. Two field *names* are established by elimination rather
    than by positional statement; both are constant in our data and neither is used as a feature, so
    the residual risk is confined to naming. Recorded because Principle V forbids presenting
    inference as fact.
