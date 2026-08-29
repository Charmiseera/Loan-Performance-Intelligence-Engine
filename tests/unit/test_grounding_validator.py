import pytest
from lpie.llm.grounding import GroundingValidator, GroundingValidationResult


def test_grounding_validator_valid_text():
    context = {
        "loan_id": "F06Q10000001",
        "credit_score": 740,
        "original_upb": 250000,
        "prob_default_12m": 0.05,
        "delinquency_status": "00",
    }
    
    generated_text = (
        "Loan F06Q10000001 has a credit score of 740 and an original balance of $250000. "
        "The predicted 12-month default risk is 0.05."
    )
    
    validator = GroundingValidator()
    result = validator.validate(generated_text, context)
    assert result.is_valid is True
    assert len(result.unresolved_claims) == 0


def test_grounding_validator_rejects_hallucinated_number():
    """
    FR-074 / Principle III:
    Inject a fabricated figure (e.g. 950 or 890000) into otherwise valid generated text
    and assert rejection.
    """
    context = {
        "loan_id": "F06Q10000001",
        "credit_score": 740,
        "original_upb": 250000,
    }
    
    # Fabricated credit score 880 (not in context)
    hallucinated_text = "Loan F06Q10000001 has a credit score of 880 and original balance 250000."
    
    validator = GroundingValidator()
    result = validator.validate(hallucinated_text, context)
    assert result.is_valid is False
    assert any("880" in claim for claim in result.unresolved_claims)
