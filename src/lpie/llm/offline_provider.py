from typing import Any, Dict, Optional
from lpie.llm.provider import BaseLLMProvider, LLMResponse


class OfflineTemplateProvider(BaseLLMProvider):
    """
    Deterministic offline template provider.
    Ensures full pipeline execution without API credentials (Principle III / FR-061).
    """

    def __init__(self, model_id: str = "offline-deterministic-v1"):
        self.model_id = model_id

    def generate(self, prompt: str, grounding_context: Optional[Dict[str, Any]] = None) -> Any:
        ctx = grounding_context or {}
        loan_id = ctx.get("loan_id", "UNKNOWN")
        credit_score = ctx.get("credit_score", "N/A")
        orig_upb = ctx.get("original_upb", "N/A")
        p_def = ctx.get("prob_default_12m", 0.0)
        p_prep = ctx.get("prob_prepay_12m", 0.0)
        exc_type = ctx.get("exception_type", "DATA_QUALITY_EXCEPTION")
        drivers = ctx.get("top_drivers", "credit_score, debt_to_income_ratio, original_ltv")
        action = ctx.get("recommended_action", "MANUAL_AUDIT")

        note = (
            f"RECOMMENDATION_REQUIRING_HUMAN_CONFIRMATION: Loan {loan_id} exhibits "
            f"12-month default risk of {p_def:.3f} and prepayment probability of {p_prep:.3f}. "
            f"Origination profile: Credit score {credit_score}, original UPB ${orig_upb}. "
            f"Flagged for {exc_type}. Key drivers: {drivers}. "
            f"Proposed action: `{action}`."
        )
        return note


# Alias for backwards compatibility
OfflineReviewerProvider = OfflineTemplateProvider
