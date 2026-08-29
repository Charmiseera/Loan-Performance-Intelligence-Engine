from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Dict, Optional


class PromptLogger:
    """
    Append-only audit logger for LLM calls.
    Stamps recommendation labels into all generated artifacts (Principle I & III / FR-058, FR-060).
    """

    def __init__(self, log_path: Path):
        self.log_path = log_path
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def log_call(
        self,
        provider: str,
        model_id: str,
        prompt: str,
        response: str,
        grounding_context: Dict[str, Any],
        is_accepted: bool,
        rejection_reasons: Optional[list] = None,
        duration_seconds: float = 0.0,
    ) -> None:
        entry = {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "provider": provider,
            "model_id": model_id,
            "duration_seconds": duration_seconds,
            "is_accepted": is_accepted,
            "rejection_reasons": rejection_reasons or [],
            "grounding_context": grounding_context,
            "prompt": prompt,
            "response": response,
            "governance_label": "RECOMMENDATION_REQUIRING_HUMAN_CONFIRMATION",
        }
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, default=str) + "\n")
