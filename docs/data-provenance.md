# Data Provenance

Constitution Principle IV requires that data provenance be documented rather than the data
committed. Principle V requires that every reported number trace to something that actually ran.
Every figure on this page was measured by a full scan of the raw files, not estimated.

## Source

| | |
|---|---|
| **Dataset** | Freddie Mac Single-Family Loan-Level Dataset — **Sample** subset |
| **Publisher** | Federal Home Loan Mortgage Corporation (Freddie Mac) |
| **Portal** | <https://www.freddiemac.com/research/datasets/sf-loanlevel-dataset> |
| **Access route** | Institution-direct, free registration with accepted terms |
| **Retrieved** | 2026-08-27 |
| **Vintages** | 2006, 2007, 2012, 2015, 2020, 2021 |
| **Release** | **47 (July 2026)** — see below |

**Release identification matters.** The 31/35 field counts do not match any published Freddie Mac
layout document: the live `user_guide.pdf` is dated January 2026 (Release 46) and documents 32/32.
Release 47 moved MI Cancellation Indicator and Servicer Name from the origination file to the
performance file, added VantageScore 4.0 to origination, and added Bankruptcy Cramdown Costs to
performance — which produces exactly 31 and 35. Freddie has **not yet published an R47 guide or
layout file**, so the field-name and coded-value reference is maintained locally at
[`docs/freddie-mac-r47-layout.md`](freddie-mac-r47-layout.md). Reading these files against the
published guide would be wrong by two columns in one file and three in the other.

**Why institution-direct**: §13 of the problem statement lists *"uses public data in violation of
source terms"* as a disqualification condition. Third-party redistributions (Kaggle mirrors of
this dataset) generally breach the portal's redistribution clause. See
[`data/raw/README.md`](../data/raw/README.md) for the full rejected-alternatives table.

> **Outstanding provenance task**: record the SHA-256 of each source archive. Not yet captured
> because the archives were extracted before hashing. If the originals are still available,
> hash them; otherwise note that hashes cover the extracted `.txt` files instead.

## Physical inventory

Files are pipe-delimited (`|`), **no header row**, one `orig` + one `perf` file per vintage.
Note the performance files are named `sample_perf_*`, **not** `sample_svcg_*` as some older
Freddie documentation states.

| File | Fields | Rows | Size |
|---|---|---|---|
| `sample_orig_2006.txt` | 31 | 50,000 | 6.4 MB |
| `sample_orig_2007.txt` | 31 | 50,000 | 6.4 MB |
| `sample_orig_2012.txt` | 31 | 50,000 | 6.5 MB |
| `sample_orig_2015.txt` | 31 | 50,000 | 6.2 MB |
| `sample_orig_2020.txt` | 31 | 50,000 | 6.2 MB |
| `sample_orig_2021.txt` | 31 | 50,000 | 6.3 MB |
| `sample_perf_2006.txt` | 35 | 3,203,499 | 341 MB |
| `sample_perf_2007.txt` | 35 | 3,012,061 | 320 MB |
| `sample_perf_2012.txt` | 35 | 4,510,559 | 468 MB |
| `sample_perf_2015.txt` | 35 | 3,467,166 | 356 MB |
| `sample_perf_2020.txt` | 35 | 2,517,857 | 263 MB |
| `sample_perf_2021.txt` | 35 | 2,537,054 | 270 MB |
| **Total** | | **300,000 loans / 19,248,196 monthly rows** | **~2.0 GB** |

Loan-sequence-number uniqueness was verified at exactly 50,000 per origination file, confirming
the documented 50,000-loan-per-vintage sample design.

Monthly reporting periods observed in the 2006 vintage span **200601–202603**, giving roughly a
20-year observation window.

## Measured label distributions

These drive the modeling strategy and are reproduced here because they justify design choices
that would otherwise look arbitrary.

### Current Loan Delinquency Status (field 4) — all 19,248,196 rows

| Code | Meaning | Rows | Share |
|---|---|---|---|
| `00` | Current | 18,543,826 | **96.3406%** |
| `01` | 1 month delinquent | 255,012 | 1.3249% |
| `02` | 2 months delinquent | 83,580 | 0.4342% |
| `03` | 3 months delinquent | 43,128 | 0.2241% |
| `RA` | REO Acquisition | 42,381 | 0.2202% |
| `04` | 4 months delinquent | 31,743 | 0.1649% |
| `05` | 5 months delinquent | 26,986 | 0.1402% |
| … | increasing months delinquent | … | long tail to `99` |

Codes are **two-character zero-padded**. The complete observed value set is `00`–`99` — **all 100
numeric values present** — plus `RA`. There are no `XX` values, no single-character values, and no
blanks. In this field `99` is a genuine 99-months-delinquent count, **not** a missingness sentinel
(unlike `99` in origination fields 7, 18, and 23). `XX` and single-character `R` belong to
pre-Release-29 files; any parser handling them was written against an obsolete layout.

The 19,248,196 row total was verified twice by independent record-count passes. A background
research pass reported 19,182,196 and a `00` share of 96.7%; that denominator is short by 66,000
rows and its percentage is therefore wrong. The figures in this table are the measured ones.

**Consequence**: a 96.34% majority class makes accuracy meaningless. Metrics must be PR-AUC,
recall at fixed precision, and Brier score — as §8 Task 2 in fact requires. Class-imbalance
handling is not an optional refinement here.

### Zero Balance Code (field 9) — termination reasons

**Verified.** Field meanings and the prepay/credit-event split were confirmed against Freddie Mac's
official Release 46 user guide and Release 47 release notes, then independently re-measured here.
Full detail, including the release-identification argument, lives in
[`docs/freddie-mac-r47-layout.md`](freddie-mac-r47-layout.md).

205,815 of 300,000 loans reached a zero balance; **94,185 (31.4%) never terminated within the
observation window and are therefore right-censored.** A full scan confirms **exactly one
zero-balance row per loan, with zero exceptions** — the code is set once, at the earliest
terminating event.

| Code | Meaning | Bucket | Loans | Actual Loss populated | `00` at termination |
|---|---|---|---|---|---|
| `01` | Prepaid or Matured | **PREPAY** | 193,126 | 0 | 98.9% |
| `09` | REO Disposition | **CREDIT** | 4,990 | 4,489 | 0.0% (`RA` 100%) |
| `03` | Short Sale or Charge Off | **CREDIT** | 2,342 | 2,188 | 3.5% |
| `02` | Third Party Sale | **CREDIT** | 1,257 | 1,220 | 2.1% |
| `15` | Non-Performing (Note) Sale | **CREDIT** | 528 | 479 | 0.4% |
| `16` | Reperforming Loan Securitization | **REMOVE** | 2,437 | 0 | 73.5% |
| `96` | Confirmed Defect prior to Disposition | **REMOVE** | 1,135 | 0 | 60.0% |

The bucketing is corroborated three independent ways rather than assumed: official documentation;
the loss fields, which are populated *only* for genuine credit events; and delinquency status at
termination, which is `00` for 98.9% of payoffs but `06`–`23` or `RA` for credit events.

> **Correction — an earlier version of this document was wrong.** It listed `15`/`16` as
> "genuinely ambiguous loan sales" requiring a judgement call, and grouped credit events as
> `09`+`03`+`02` = 8,589. That was based on pre-Release-35 domain knowledge. Release 35 (April 2023)
> **split** the old whole-loan-sale code: `15` retained Non-Performing (Note) Sales **with losses
> disclosed**, while `16` took Reperforming Loan Securitizations **with no losses**. So `15` is a
> credit event and `16` is not, and the correct credit-event total is **9,117**. Code `96` loans
> have all loss fields zeroed by design (Release 32) and are administrative repurchases, not
> zero-loss defaults, so they are removed rather than counted either way.

### Resulting label population

| Outcome | Loans | Share of label population |
|---|---|---|
| Prepay (`01`) | 193,126 | 65.15% |
| Credit event (`02`,`03`,`09`,`15`) | **9,117** | **3.08%** |
| Right-censored (blank) | 94,185 | 31.77% |
| Removed (`16`,`96`) — neither outcome | 3,572 | *excluded* |
| **Label population** | **296,428** | 100% |

**Consequence**: roughly 65% of loans prepay while roughly 3% experience a credit event. Two events
compete for the same loan and the more common one censors the rarer one. Modeling default with
prepayment ignored would be a specification error, which is why §8 Task 3's "competing-risk
approximation" is the correct frame rather than a stretch goal.

### Loss-mitigation regimes

| Field | Value | Rows |
|---|---|---|
| Modification Flag (8) | `P` payment deferral | 472,662 |
| Modification Flag (8) | `Y` modified | 8,391 |
| Borrower Assistance (30) | `F` forbearance | 49,568 |
| Borrower Assistance (30) | `T` trial modification | 14,312 |
| Borrower Assistance (30) | `R` repayment plan | 6,354 |

**Consequence**: the 2020/2021 vintages carry COVID-era forbearance, which is a genuine regime
shift from the 2006/2007 crisis vintages. This is a real source of train/test drift for §8
Task 1 rather than a synthetic one.

## Zero-variance origination fields

> **Correction — an earlier version of this document was wrong.** It claimed origination positions
> **25–31** were all zero-variance and could be dropped. That measurement was taken on the **2006
> vintage only** and then generalised, which was an error: five of those seven fields vary once all
> six vintages are pooled, and two of them are among the most informative fields in the dataset.
> The table below is measured across all 300,000 origination rows.

| Pos | Field | Verdict | Evidence across vintages |
|---|---|---|---|
| 25 | Super Conforming Flag | **varies** | `N` only in 2006/2007; `Y` 1,452 / 2,040 / 2,570 / 1,770 in 2012/2015/2020/2021 — zero `Y` before the Oct-2008 program start |
| 26 | Pre-HARP Loan Sequence Number | **varies** | filled 17,399 (2012), 4,017 (2015), zero elsewhere |
| 27 | Program Indicator | **varies** | blank until 2015; then `H` 311/1,836/1,674, `F` 14/158/116, `R` 15 (2021 only) |
| 28 | HARP Indicator | **varies** | `Y` 17,399 (2012), 4,017 (2015), zero elsewhere |
| 29 | Property Valuation Method | **varies** | `7` (N/A) through 2015; `2`:30,684 `1`:19,316 (2020), `2`:31,396 `1`:18,604 (2021) |
| 30 | Interest Only Indicator | **zero-variance** | `N` in all 300,000 rows |
| 31 | VantageScore 4.0 | **zero-variance** | `9999` in all 300,000 rows |

Positions 26 and 28 are mutually corroborating: Pre-HARP sequence number is filled in **exactly**
the 17,399 and 4,017 rows where HARP Indicator is `Y`. Position 29 becoming populated only from the
2020 vintage matches its documented start date of 2017-01-01. These internal consistencies are
independent evidence that the position assignments are correct.

**Genuinely droppable as zero-variance** (measured across all 300,000 rows): position 16
Amortization Type (`FRM` throughout — the Standard Dataset is fixed-rate only), position 30
Interest Only Indicator, position 31 VantageScore 4.0. Exclusion of these three is recorded here so
the choice is auditable rather than silent.

**Not droppable**: positions 25–29 carry real signal. HARP status and Pre-HARP linkage identify a
structurally distinct refinance population; Program Indicator flags affordability-program loans;
Property Valuation Method distinguishes appraisal-waiver originations. Dropping them would have
discarded genuine predictive information on the basis of a single-vintage measurement.

## Schema gap versus the problem statement

§6 describes an organizer-provided pack of eight files. Freddie raw supplies the equivalent of
two of them. The remainder must be **constructed** and that construction must be declared
honestly, since §13 penalizes fabricated results.

| §6 file | Status against Freddie raw |
|---|---|
| `loan_monthly_performance_train.csv` | **Derived** from `sample_perf_*` + `sample_orig_*`, mapped to §7 field names |
| `loan_static_attributes.csv` | **Derived** from `sample_orig_*` |
| `loan_monthly_performance_test.csv` | **Derived** by time-aware holdout, labels withheld |
| `data_dictionary.md` | **Authored** — no Freddie equivalent; needed for LLM grounding |
| `validation_rules.json` | **Authored** — deterministic checks per §6 |
| `submission_template.csv` | **Authored** from the §7 target list |
| `macro_scenarios.csv` | **Authored** — assumptions must be labelled as stated assumptions, not observed data |
| `servicer_updates.csv` | **No source equivalent.** Freddie has one authoritative record per loan-month, so genuine cross-source conflict does not exist in it. Any conflict file is necessarily constructed and MUST be labelled a synthetic reconciliation fixture in the model card. Presenting constructed conflicts as observed data would violate Principle V. |

**Servicer transfers are real, conflicts are not.** Release 47 moved Servicer Name into the
performance file (field 34), where it genuinely **varies month to month** as servicing is
transferred — 53 distinct servicers in the 2006 vintage against 34 in 2021. That is a legitimate
time-varying attribute, not a source disagreement, so it does not change the conclusion above: the
reconciliation fixture remains constructed. It does mean the fixture can be built on top of
realistic transfer patterns rather than invented ones, and it means any "by servicer" segmentation
must be **as-of-month aware** rather than treating servicer as a static loan attribute.

Field-name translation from the Freddie layout to the §7 names lives in the schema configuration,
so swapping to a real organizer pack is a configuration change rather than a code change
(Principle IV).
