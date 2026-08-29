from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class LLMResponse:
    text: str
    model_id: str = "offline-deterministic-v1"
    provider: str = "offline"
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class BaseLLMProvider(ABC):
    """Abstract interface for LLM Copilot providers."""

    @abstractmethod
    def generate(self, prompt: str, grounding_context: Optional[Dict[str, Any]] = None) -> Any:
        """Generate text given a prompt and grounding context."""
        pass
