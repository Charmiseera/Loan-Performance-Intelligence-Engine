# Freddie Mac Single-Family Loan-Level Dataset — Release 47 Layout Reference

**Purpose**: this is the authoritative field-name and coded-value source that the schema
configuration is generated from. Constitution Principle IV requires field-name translation to live
in configuration rather than code; that configuration has to be derived from *something*, and this
is it.

**Why a local document**: Freddie Mac has **not published a user guide or machine-readable layout
for Release 47**. The live `user_guide.pdf` is dated January 2026 (Release 46) and documents
**32 origination / 32 performance** fields. Our files carry **31 / 35**. Pointing the schema config
at the published guide would therefore be wrong by two columns in one file and three in the other.

## Evidence markers

Every row below carries an evidence marker. Principle V forbids presenting inference as fact.

| Marker | Meaning |
|---|---|
| **[D]** | Stated in an official Freddie Mac document (cited below) |
| **[E]** | Position confirmed empirically against our own six vintages |
| **[I]** | **Inferred** by elimination — name not positionally confirmed by any document |

## Sources

| Document | URL | Date / release |
|---|---|---|
| General User Guide | <https://www.freddiemac.com/fmac-resources/research/pdf/user_guide.pdf> | Jan 2026 / R46 |
| Machine-readable layout | <https://www.freddiemac.com/fmac-resources/research/pdf/file_layout.xlsx> | 2023-04-04 |
| Release Notes | <https://www.freddiemac.com/fmac-resources/research/pdf/release_notes.pdf> | Jul 2026 / R47 |

---

## Release identification: our files are R47

The 31/35 field counts are explained exactly by the R47 release notes **[D]**:

| File | R46 | R47 change | R47 |
|---|---|---|---|
| Origination | 32 | − MI Cancellation Indicator, − Servicer Name (both moved to performance); + VantageScore 4.0 | **31** |
| Performance | 32 | + MI Cancellation Indicator, + Servicer Name (moved from origination); + Bankruptcy Cramdown Costs | **35** |

R47 additionally applies "enumeration updates" to several fields and **inverts the sign convention
on loss elements**. Both matter and are covered below.

> ⚠ **`release_notes.pdf` contains a legacy data dictionary as an appendix** describing a pre-R29
> layout (credit score range `301–850`, `000 = No MI`, blank-space sentinels). It must **not** be
> used for these files.

---

## 1. Origination file — `sample_orig_YYYY.txt`, 31 fields

| # | Field | Type | Codes and sentinels | Ev. |
|---|---|---|---|---|
| 1 | Credit Score | Num(4) | 300–850; **`9999` = Not Available** | D+E |
| 2 | First Payment Date | YYYYMM | | D+E |
| 3 | First Time Homebuyer Flag | Alpha(1) | `Y`/`N`/`9` = N/A | D+E |
| 4 | Maturity Date | YYYYMM | | D+E |
| 5 | MSA or Metropolitan Division | Num(5) | blank = not in an MSA **or** unknown | D+E |
| 6 | Mortgage Insurance Percentage | Num(3) | 1–55; **`0` = No MI (not missing)**; **`999` = Not Available** | D+E |
| 7 | Number of Units | Num(2) | 1–4; **`99` = Not Available** | D+E |
| 8 | Occupancy Status | Alpha(1) | `P` Primary, `I` Investment, `S` Second home, `9` N/A | D+E |
| 9 | Original CLTV | Num(3) | **`999` = Not Available** (also set when CLTV < LTV) | D+E |
| 10 | Original DTI | Num(3) | 0 < DTI ≤ 65; **`999` = Not Available** (all HARP loans) | D+E |
| 11 | Original UPB | Num(12) | rounded to nearest $1,000 | D+E |
| 12 | Original LTV | Num(3) | **`999` = Not Available** | D+E |
| 13 | Original Interest Rate | Num(6,3) | `6.5` — **not** zero-padded (contrast perf 11) | D+E |
| 14 | Channel | Alpha(1) | `R` Retail, `B` Broker, `C` Correspondent, `T` TPO unspecified, `9` N/A | D+E |
| 15 | Prepayment Penalty Mortgage Flag | Alpha(1) | `Y`/`N` | D+E |
| 16 | Amortization Type | Alpha(5) | `FRM`/`ARM` — **`FRM` in 100% of our rows** | D+E |
| 17 | Property State | Alpha(2) | USPS, 54 distinct incl. DC/PR/GU/VI | D+E |
| 18 | Property Type | Alpha(2) | `SF`,`CO`,`PU`,`MH`,`CP`; `99` = N/A | D+E |
| 19 | Postal Code | Num | **R47: first 3 ZIP digits** (`757`, `028`) — guide's `###00` form is stale. Keep as string. | D+E |
| 20 | **Loan Sequence Number** | AlphaNum(12) | `PYYQnXXXXXXX` — **the join key** | D+E |
| 21 | Loan Purpose | Alpha(1) | `P` Purchase, `C` Cash-out refi, `N` No-cash-out refi, `R` Refi unspecified, `9` N/A | D+E |
| 22 | Original Loan Term | Num(3) | (Maturity − First Payment) + 1 month | D+E |
| 23 | Number of Borrowers | Num(2) | **R47: unpadded** `1`–`5`; **`99` = Not Available**. Pre-2018Q2: `01` = 1, `02` = >1 | D+E |
| 24 | Seller Name | AlphaNum(60) | real name if ≥1% of quarterly UPB, else **`OTHER`** | D+E |
| 25 | Super Conforming Flag | Alpha(1) | **R47: `Y`/`N`** (old form was `Y`/space) | D+E |
| 26 | Pre-HARP Loan Sequence Number | AlphaNum(12) | sequence number of the refinanced loan; blank otherwise | D+E |
| 27 | Program Indicator | AlphaNum(1) | `H` Home Possible, `F` HFA Advantage, `R` Refi Possible, blank/`9` N/A | D+E |
| 28 | HARP Indicator | Alpha(1) | **R47: `Y`/`N`**. HARP = Relief Refi **and** Original LTV > 80 | D+E |
| 29 | Property Valuation Method | Num(1) | `1` Appraisal Waiver (ACE), `2` Appraisal, `3` Other, `4` ACE+PDR, `7` N/A — **codes were redefined in R46** | D+E |
| 30 | Interest Only Indicator | Alpha(1) | `Y`/`N` — **`N` in 100% of our rows** | D+E |
| 31 | VantageScore 4.0 | Num(4) | **`9999` in 100% of our rows** | D + **[I]** |

---

## 2. Performance file — `sample_perf_YYYY.txt`, 35 fields

| # | Field | Type | Codes and sentinels | Ev. |
|---|---|---|---|---|
| 1 | **Loan Sequence Number** | AlphaNum(12) | join key to orig 20 | D+E |
| 2 | **Monthly Reporting Period** | YYYYMM | **the as-of month; the temporal split key** | D+E |
| 3 | Current Actual UPB | Num(12,2) | **rounded to nearest $1,000 for the first six payment periods**; not rounded after modification | D+E |
| 4 | **Current Loan Delinquency Status** | AlphaNum(3) | see §3 | D+E |
| 5 | Loan Age | Num(3) | **resets to modification first-payment date for modified loans**; not reset by payment deferral | D+E |
| 6 | Remaining Months to Legal Maturity | Num(3) | uses modified maturity date when Modification Flag ∈ {`Y`,`P`} | D+E |
| 7 | Defect Settlement Date | YYYYMM | blank = no defect (replaced Repurchase Flag in R29) | D+E |
| 8 | Modification Flag | Alpha(1) | `Y` modified this period, `P` prior-period modification, blank = not modified | D+E |
| 9 | **Zero Balance Code** | Num(2) | see §4 — **the termination label** | D+E |
| 10 | Zero Balance Effective Date | YYYYMM | blank = N/A | D+E |
| 11 | Current Interest Rate | Num(8,3) | zero-padded `6.500` | D+E |
| 12 | Current Deferred UPB | Num(12) | `0.00` when none — **never blank** | D+E |
| 13 | Due Date of Last Paid Installment | YYYYMM | blank except on terminating records | D+E |
| 14 | MI Recoveries | Num(12,2) | **NEGATIVE in R47** | D+E |
| 15 | Net Sales Proceeds | AlphaNum(14) | **NEGATIVE in R47**; `U` = Unknown (documented, not observed) | D+E |
| 16 | Non MI Recoveries | Num(12,2) | **NEGATIVE in R47** | D+E |
| 17 | Expenses | Num(12,2) | positive; aggregate of 18–21 | D+E |
| 18 | Legal Costs | Num(12,2) | positive | D+E |
| 19 | Maintenance and Preservation Costs | Num(12,2) | positive | D+E |
| 20 | Taxes and Insurance | Num(12,2) | positive | D+E |
| 21 | Miscellaneous Expenses | Num(12,2) | positive | D+E |
| 22 | **Actual Loss Calculation** | Num(12,2) | **populated only for ZB ∈ {02,03,09,15}** — the credit-event corroborator | D+E |
| 23 | Modification Cost | Num(12,2) | R47: disclosed every month (was last record only) | D+E |
| 24 | Interest Rate Step Indicator | Alpha(1) | `Y` step mod, `N` non-step mod, blank = not modified | D+E |
| 25 | Payment Deferral Flag | Alpha(1) | **R47: `C` current period, `P` prior period**, blank = none. Guide's `Y` is stale | D+E |
| 26 | Estimated Loan-to-Value (ELTV) | Num(4) | 1–998; **`999` = Unknown, and carried for all pre-Apr-2017 periods** | D+E |
| 27 | Zero Balance Removal UPB | Num(12,2) | UPB immediately before the zero-balance code applied | D+E |
| 28 | Delinquent Accrued Interest | Num(12,2) | only for ZB ∈ {02,03,09,15}; positive | D+E |
| 29 | Delinquency Due to Disaster | Alpha(1) | `Y`, blank = no. Populated Jan 2014+ | D+E |
| 30 | Borrower Assistance Status Code | Alpha(1) | `F` Forbearance, `R` Repayment, `T` Trial Period, blank = none. Jan 2014+ | D+E |
| 31 | Current Month Modification Cost | Num(12,2) | | D+E |
| 32 | Interest Bearing UPB | Num(12,2) | `0.00` never blank | D+E |
| 33 | MI Cancellation Indicator | Alpha(1) | `Y` Canceled, `N` Not canceled, `7` N/A, `9` Not disclosed. **Moved from orig in R47** | D+E |
| 34 | **Servicer Name** | AlphaNum(60) | real name if ≥1% of quarterly UPB else `OTHER`. **Moved from orig in R47 — now time-varying per month** | D+E |
| 35 | Bankruptcy Cramdown Costs | Num(12,2) | blank / `0.00` / dollar amounts | D + **[I]** |

Position 33 was confirmed by an exact value-set match across 19.2M rows
(`7`: 17,369,465 / `N`: 1,538,192 / `Y`: 340,539). Position 34 was confirmed by real servicer
names that **change month-to-month within a loan** — impossible for an origination field.

---

## 3. Current Loan Delinquency Status (performance field 4)

**[D]** Value = months delinquent under the MBA method, derived from Due Date of Last Paid
Installment. **[E]** In our R47 files the codes are **two-character zero-padded**. The complete
observed value set across all rows is `00`–`99` (**all 100 numeric values present**) plus `RA`.
**Nothing else — no `XX`, no single-character values, no blanks.**

| Code | Meaning |
|---|---|
| `00` | Current, or < 30 days delinquent |
| `01`…`99` | *n* payments past due (`99` is a **real count, not a sentinel**) |
| `RA` | **REO Acquisition** — status reflects REO, not days delinquent |

Decoding rule: `months_delinquent = int(status)` for numeric codes; `RA` handled separately.

> `XX` (Unknown) and single-character `R` (REO Acquisition) belong to **pre-R29** releases. R29
> (Oct 2021) changed `R` → `RA` and added performance records covering the months between REO
> acquisition and REO disposition. Any parser handling `XX`/`R`/space was written against an
> obsolete layout.

---

## 4. Zero Balance Code (performance field 9) — the prepay/default split

**[D]** Release 46 guide, Zero Balance Codes section, including the termination-event priority
table. The code is set **at most once per loan**, at the earliest terminating event; priority 1
wins when two events fall in the same period.

| Code | Reason for termination | Priority | **Bucket** |
|---|---|---|---|
| `15` | Whole Loan Sale — in practice **Non-Performing (Note) Sale** | 1 | **CREDIT EVENT** |
| `16` | Reperforming Loan Securitization | 2 | **REMOVE** — administrative, no losses |
| `09` | REO Disposition | 3 | **CREDIT EVENT** |
| `96` | Confirmed Defect prior to Property Disposition | 4 | **REMOVE** — repurchase, loss fields zeroed |
| `03` | Short Sale or Charge Off | 5 | **CREDIT EVENT** |
| `02` | Third Party Sale | 6 | **CREDIT EVENT** |
| `01` | Prepaid or Matured (voluntary payoff) | 7 | **PREPAYMENT** |

### Empirical corroboration [E]

The bucketing is not a judgement call. Actual Loss and Net Sales Proceeds are populated *only* for
genuine credit events, which independently confirms every assignment:

| ZB | Loans | Actual Loss populated | Net Sales Proceeds populated | Delinquency status at termination |
|---|---|---|---|---|
| `01` | 193,126 | **0** | **0** | `00` in 98.9% |
| `02` | 1,257 | 1,220 | 1,220 | `10`–`15` (deep) |
| `03` | 2,342 | 2,188 | 2,188 | `06`–`11` |
| `09` | 4,990 | 4,489 | 4,489 | **`RA` in 100%** |
| `15` | 528 | 479 | 479 | `17`–`23` (very deep) |
| `16` | 2,437 | **0** | **0** | `00` 73%, `01` 15%, `02` 9% |
| `96` | 1,135 | **0** | **0** | mixed, `00` 60% |

### The modeling rule

```
PREPAY        : zero_balance_code == '01'
CREDIT EVENT  : zero_balance_code in ('02', '03', '09', '15')
REMOVE        : zero_balance_code in ('16', '96')   # neither outcome; drop from label population
STILL ACTIVE  : zero_balance_code is blank          # right-censored at last observed month
```

### Codes that do not exist here

- **`06` was retired.** **[D]** R29 replaced `06` with `96` for CRT alignment. Absent from the R46
  valid-value list and from every one of our rows.
- **`97` and `98` are not Freddie Mac codes.** They belong to the **Fannie Mae** dataset
  (97 = delinquency-related disposition, 98 = other). Absent from documentation and from our data.
- **`16` is post-R35.** **[D]** R35 (Apr 2023): Reperforming Loan Sales moved from `15` to `16`
  with **no losses disclosed**, while Non-Performing (Note) Sales stayed at `15` **with** losses.
  This is why `15` is a credit event and `16` is not — and why pre-R35 code that treated `15` as a
  benign whole-loan sale **understates defaults**.

---

## 5. Sentinel value summary

| Sentinel | Fields |
|---|---|
| `9999` | Credit Score (o1), VantageScore4 (o31) |
| `999` | MI % (o6), CLTV (o9), DTI (o10), LTV (o12); ELTV (p26) — **also carried for all pre-Apr-2017 periods** |
| `99` | Number of Units (o7), Number of Borrowers (o23), Property Type (o18). **⚠ In p4, `99` is a real 99-months-delinquent count, NOT a sentinel.** |
| `9` | First Time Homebuyer (o3), Occupancy (o8), Channel (o14), Loan Purpose (o21), Program Indicator (o27), MI Cancellation (p33 = Not Disclosed) |
| `7` | Property Valuation Method (o29) = N/A; MI Cancellation (p33) = Not Applicable |
| `0` | MI % (o6) = **No MI — not missing** |
| `00` | Postal Code (o19) = Unknown |
| blank | MSA (o5), Pre-HARP Seq (o26), Program Indicator (o27); perf 7–10, 13–25, 27–31, 35 |
| `0.00` | Current Deferred UPB (p12), Interest Bearing UPB (p32) — use `0.00`, never blank |
| `U` | Net Sales Proceeds (p15) = Unknown (documented, not observed here) |

---

## 6. Traps that silently corrupt a pipeline

Each of these is a concrete defect the ingest layer must handle, and several are the reason
Principle II's leakage-audit artifact is emitted every run.

1. **Loss-element signs are inverted versus every pre-R47 release.** Recoveries and proceeds are
   **negative**; expenses and losses are **positive**. The R46 guide's formula
   `Actual Loss = (ZB Removal UPB − Net Sale Proceeds) + Delinquent Accrued Interest − Expenses −
   MI Recoveries − Non MI Recoveries` **no longer holds as written**. Use field 22 directly.
2. **Payment Deferral Flag is `C`/`P`, not `Y`/`P`.** Zero `Y` values exist in our data.
3. **Delinquency status is two-character zero-padded.** Comparing `== '0'` matches nothing.
4. **Servicer Name is not in the origination file.** It is performance field 34 and **varies by
   month**, so any "by servicer" segmentation must be as-of-month aware, not static.
5. **Postal Code is a 3-digit prefix**, not a 5-digit ZIP. Leading zeros (`028`) require string
   handling.
6. **`ZB == '15'` is a credit event; `ZB == '16'` is not.**
7. **`ZB == '96'` loans have all loss fields zeroed** **[D]** (R32). They are not zero-loss
   defaults — drop them.
8. **Loan Age resets on modification** but not on payment deferral, so it is not a clean seasoning
   variable for modified loans.
9. **Current Actual UPB is rounded to the nearest $1,000 for the first six payment periods.**
10. **Interest-rate formatting differs between files**: `6.5` in origination, `6.500` in
    performance. Cast both.
11. **Property Valuation Method codes were redefined in R46.**
12. **Amortization Type is `FRM` in 100% of rows and Interest Only Indicator is `N` in 100%** —
    the Standard Dataset is fully-amortizing fixed-rate only. Both are genuinely zero-variance.

---

## 7. What is inferred rather than verified

Because no R47 guide or layout file has been published, two field **names** rest on elimination
rather than an official positional statement. Positions and semantics of everything else are either
quoted from an official document or proven against our own rows.

1. **Origination 31 = VantageScore 4.0.** Confidence high: positions 1–30 are each positively
   identified by value pattern and match R46 order with positions 25 and 32 excised; R47 adds
   exactly one origination field; and the value is uniformly `9999`, the Not-Available sentinel.
   **Residual risk**: the field is 100% sentinel in our vintages, so it cannot be discriminated by
   content. It carries no information here either way.
2. **Performance 35 = Bankruptcy Cramdown Costs.** Confidence high: it is the only unaccounted
   position and R47 adds exactly one performance field. **Unknown**: whether it is already included
   in Expenses (field 17) or additive to it. **Do not sum field 35 into field 17** without checking
   a terminated-loan example.
3. **Field names generally.** R47 states "Updated field names" for both files. The names above are
   the R46 guide and layout-file names. Actual R47 strings may differ cosmetically. This affects
   naming only, not position or semantics — and since Principle IV routes all naming through the
   schema configuration, a cosmetic rename is a config edit.

**Follow-up**: re-check <https://www.freddiemac.com/research/datasets/sf-loanlevel-dataset> for an
updated `user_guide.pdf` / `file_layout.xlsx` to close items 1 and 2.
