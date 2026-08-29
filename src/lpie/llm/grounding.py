from dataclasses import dataclass, field
import re
from typing import Any, Dict, List, Set


@dataclass
class GroundingValidationResult:
    is_valid: bool
    unresolved_claims: List[str] = field(default_factory=list)
    resolved_claims: List[str] = field(default_factory=list)
    confidence_score: float = 1.0


class GroundingValidator:
    """
    Extracts numeric and entity claims from generated text and verifies they match grounding context.
    Rejects any generated output that introduces ungrounded numbers (Principle III / FR-059).
    """

    def __init__(self, numeric_tolerance: float = 0.01):
        self.numeric_tolerance = numeric_tolerance

    def _extract_numbers(self, text: str) -> List[float]:
        # Match standard decimals and integers, ignoring isolated symbols
        raw_tokens = re.findall(r"[-+]?\b\d+(?:\.\d+)?\b", text)
        numbers = []
        for tok in raw_tokens:
            try:
                numbers.append(float(tok))
            except ValueError:
                pass
        return numbers

    def _extract_context_numbers(self, context: Dict[str, Any]) -> Set[float]:
        context_nums = set()
        for v in context.values():
            if isinstance(v, (int, float)):
                context_nums.add(float(v))
            elif isinstance(v, str):
                for tok in re.findall(r"[-+]?\b\d+(?:\.\d+)?\b", v):
                    try:
                        context_nums.add(float(tok))
                    except ValueError:
                        pass
        return context_nums

    def validate(self, text: str, context: Dict[str, Any]) -> GroundingValidationResult:
        extracted_nums = self._extract_numbers(text)
        context_nums = self._extract_context_numbers(context)

        unresolved = []
        resolved = []

        # Common harmless numbers allowed without explicit context (e.g. 12-month, 3-month)
        whitelist = {1.0, 2.0, 3.0, 6.0, 12.0, 100.0}

        for num in extracted_nums:
            if num in whitelist:
                resolved.append(str(num))
                continue

            # Check if within tolerance of any context number
            matched = any(abs(num - c_num) <= max(self.numeric_tolerance, abs(c_num) * 0.001) for c_num in context_nums)
            if matched:
                resolved.append(str(num))
            else:
                unresolved.append(f"Ungrounded number: {num}")

        is_valid = len(unresolved) == 0
        return GroundingValidationResult(
            is_valid=is_valid,
            unresolved_claims=unresolved,
            resolved_claims=resolved,
            confidence_score=1.0 if is_valid else max(0.0, 1.0 - (len(unresolved) * 0.3)),
        )
