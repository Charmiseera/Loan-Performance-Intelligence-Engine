# `data/raw/` — Source Data Drop Zone

Nothing in this directory is committed (see [`.gitignore`](../../.gitignore)). Constitution
Principle IV forbids committing data files; provenance is recorded here instead.

## What to put here

**Source**: Freddie Mac Single-Family Loan-Level Dataset — **Sample** subset
**Portal**: <https://www.freddiemac.com/research/datasets/sf-loanlevel-dataset>
**Access**: Free registration, instant. Choose *Sample Datasets*, **not** Full (~100 GB).

### Why this source

It is the only freely available source providing the **monthly panel structure** the problem
statement requires in §6 (`loan_monthly_performance_train.csv` — "one row per loan per month").
Alternatives were rejected:

| Source | Rejected because |
|---|---|
| HMDA (`ffiec.cfpb.gov`) | Application-level, one row per loan. No monthly performance, no delinquency outcomes → cannot support Task 2 or Task 3. Retained as an optional geography/attribute supplement only. |
| Lending Club (Kaggle) | One row per loan, no panel. Also a third-party redistribution. |
| Kaggle mirrors of Freddie/Fannie | §13 lists *"uses public data in violation of source terms"* as a **disqualification condition**. Re-uploads generally breach the redistribution clause. Institution-direct only. |
| Fannie Mae Data Dynamics | Equivalent structure and also acceptable, but a heavier portal flow. Use as fallback if Freddie registration stalls. |

### Vintages to download

| File | Why this vintage matters |
|---|---|
| `sample_2006.zip` | Crisis-era. Supplies real defaults — without it `next_12m_default_flag` has almost no positive class. |
| `sample_2007.zip` | Crisis-era. Peak severe delinquency and loss severity. |
| `sample_2012.zip` | Recovery era. Heavy refinancing → strong prepayment signal. |
| `sample_2015.zip` | Benign credit, continued refi activity. |
| `sample_2020.zip` | Rate shock + forbearance patterns. |
| `sample_2021.zip` | Recent regime → creates genuine **train/test drift** for Task 1. |

Unzip all of them directly into this directory. Expected result:

```text
data/raw/
├── sample_orig_2006.txt      # origination / static attributes, 31 fields, pipe-delimited, NO header
├── sample_perf_2006.txt      # monthly performance, 35 fields, pipe-delimited, NO header
├── sample_orig_2007.txt
├── sample_perf_2007.txt
└── ...                       # one orig + one perf pair per vintage
```

The performance files are named `sample_perf_*`, **not** `sample_svcg_*` as some older Freddie
documentation states.

Files are pipe-delimited (`|`) with **no header row**. The 31/35 field counts identify these as
**Release 47 (July 2026)**, for which Freddie has published no layout document — the live user guide
is Release 46 and documents 32/32. Column order is therefore defined by
[`docs/freddie-mac-r47-layout.md`](../../docs/freddie-mac-r47-layout.md), which the loader encodes
explicitly rather than guessing. Reading these files against the published guide would be wrong by
two columns in one file and three in the other.

## Provenance to record

When the download completes, note the following in `docs/data-provenance.md` (Principle IV):

- Retrieval date
- Exact portal URL and subset name (*Sample*)
- Terms accepted at registration
- SHA-256 of each archive
- Vintages obtained and row counts after parsing

## If the real organizer data pack arrives instead

The §6 pack (`loan_monthly_performance_train.csv`, `loan_static_attributes.csv`,
`servicer_updates.csv`, `macro_scenarios.csv`, `data_dictionary.md`,
`validation_rules.json`, `submission_template.csv`) supersedes this. Drop it here and point
the config's dataset profile at it — every downstream module reads the schema from config, so
this is a configuration change, not a code change.
