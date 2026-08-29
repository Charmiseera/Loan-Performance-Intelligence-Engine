# Curated LLM Failure & Rejection Catalog

**Challenge**: Intain Campus FinTech Challenge 2026 — AI Track  
**Governance Requirement**: FR-062, SC-022, Principle III (Grounded LLM Governance)  
**Status**: Maintained append-only audit trail

> All natural-language outputs produced by the LLM reviewer copilot are subject to the **Grounding Validator** (`src/lpie/llm/grounding.py`). Any text containing ungrounded numbers, fabricated metrics, or speculative advice is rejected and retained in this log.

---

## Case Study 1 — Hallucinated Numeric Claim (Detected & Rejected)

- **Date**: 2026-08-28 20:15:30 UTC
- **Model**: `qwen-2.5-32b` (via Groq)
- **Task**: Reviewer case note generation for Loan `LOAN_0042`
- **Supplied Grounding Context**:
  - `loan_id`: `LOAN_0042`
  - `current_upb`: `$214,500.00`
  - `prob_default_12m`: `0.0842` (8.42%)
  - `prob_deterioration_3m`: `0.1120` (11.20%)
  - `credit_score`: `642`
  - `exception_type`: `DATA_QUALITY_EXCEPTION`
- **Generated LLM Output**:
  > *"Loan LOAN_0042 shows moderate stress with a 12-month default probability of 8.42% and unpaid balance of $214,500. **The borrower has a 24.5% likelihood of refinancing within 6 months**, and credit score is 642."*
- **Failure Detected**:
  - **Ungrounded Claim**: The number `24.5%` was fabricated by the model (not present in grounding context or model predictions).
- **Grounding Validator Verdict**: `REJECTED`
- **Rejection Reason**: `Numeric claim '24.5' not found in grounding context dictionary.`
- **Resolution**: Note discarded; deterministic grounded fallback summary substituted:
  > *"RECOMMENDATION_REQUIRING_HUMAN_CONFIRMATION: Loan LOAN_0042 presents 12-month default risk of 8.42% (3m deterioration: 11.20%) with current balance $214,500. Flagged for DATA_QUALITY_EXCEPTION. Human audit recommended."*

---

## Case Study 2 — Overconfident Policy Recommendation (Detected & Corrected)

- **Date**: 2026-08-28 21:04:12 UTC
- **Model**: `qwen-2.5-32b`
- **Task**: Action recommendation for modified delinquent mortgage
- **Generated LLM Output**:
  > *"The servicer MUST immediately initiate foreclosure proceedings under Fannie/Freddie guidelines as the loan is 90 days past due."*
- **Failure Detected**:
  - **Directive language violating Principle I**: The LLM attempted to command an action (`MUST immediately initiate foreclosure`) instead of producing a human-review recommendation.
- **Grounding Validator Verdict**: `REJECTED`
- **Rejection Reason**: `Imperative executive command detected without mandatory disclaimer.`
- **Resolution**: Pre-prompt system instruction updated with mandatory prefix: `RECOMMENDATION_REQUIRING_HUMAN_CONFIRMATION`. All output labeled non-binding.

---

## Case Study 3 — Ambiguous Termination Mapping Inference (Detected & Corrected)

- **Date**: 2026-08-27 19:30:00 UTC
- **Task**: Automated dataset layout parsing
- **AI Tool**: Antigravity Assistant
- **Failure Detected**:
  - Inferred that zero-balance codes `06` and `09` were both ambiguous loss events.
- **Human Correction**:
  - Human reviewer checked Freddie Mac R47 official documentation and proved `09` is a credit event with disclosed losses, while `06` is repurchased/administrative.
- **Result**: Documented in `spec.md` Assumption 2 and prevented 39% label noise in training set.

---

*Summary: Grounding validator enforces zero-tolerance policy on hallucinated numerical claims and unauthorized automated decisions.*
