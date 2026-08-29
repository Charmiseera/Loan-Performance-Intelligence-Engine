import os
import re
import json
import logging
from typing import Any, Dict, Optional
from lpie.llm.offline_provider import OfflineReviewerProvider
from lpie.llm.provider import BaseLLMProvider, LLMResponse

logger = logging.getLogger(__name__)


def _clean_reasoning_tags(text: str) -> str:
    """Removes internal <think>...</think> chain-of-thought blocks if present."""
    if "</think>" in text:
        return text.split("</think>")[-1].strip()
    if "<think>" in text:
        if "RECOMMENDATION_REQUIRING_HUMAN_CONFIRMATION:" in text:
            idx = text.rfind("RECOMMENDATION_REQUIRING_HUMAN_CONFIRMATION:")
            return text[idx:].strip()
        return re.sub(r"<think>.*", "", text, flags=re.DOTALL).strip()
    return text.strip()


class GroqQwenProvider(BaseLLMProvider):
    """
    Live Groq API provider with Qwen model integration (FR-057, SC-020).
    Implements comprehensive exception handling for rate limits, authentication errors,
    network timeouts, and API errors, gracefully degrading to deterministic offline
    provider without pipeline disruption (Principle III / FR-061).
    """

    def __init__(
        self,
        model_id: str = "qwen/qwen3.6-27b",
        api_key: Optional[str] = None,
        temperature: float = 0.2,
    ):
        self.model_id = model_id
        self.api_key = api_key or os.environ.get("GROQ_API_KEY")
        self.temperature = temperature
        self.offline_fallback = OfflineReviewerProvider(model_id="offline-deterministic-v1")

    def generate(self, prompt: str, grounding_context: Optional[Dict[str, Any]] = None) -> LLMResponse:
        if not self.api_key:
            # Fallback to offline provider per Principle I & FR-061
            text = self.offline_fallback.generate(prompt, grounding_context)
            return LLMResponse(
                text=str(text),
                model_id="offline-deterministic-v1",
                provider="offline_fallback",
                prompt_tokens=len(prompt) // 4,
                completion_tokens=len(str(text)) // 4,
                total_tokens=(len(prompt) + len(str(text))) // 4,
            )

        system_instruction = (
            "You are an institutional mortgage reviewer copilot. "
            "All output MUST start with: 'RECOMMENDATION_REQUIRING_HUMAN_CONFIRMATION: '. "
            "You MUST only cite facts, numbers, and probabilities explicitly present in the prompt. "
            "Never invent or hallucinate ungrounded numbers. Keep response concise (2-4 sentences)."
        )

        # 1. Attempt using official Groq SDK with full exception handling
        try:
            from groq import (
                Groq,
                AuthenticationError,
                RateLimitError,
                APIConnectionError,
                APIStatusError,
                BadRequestError,
            )

            client = Groq(api_key=self.api_key)

            completion = client.chat.completions.create(
                model=self.model_id,
                messages=[
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": prompt},
                ],
                temperature=self.temperature,
                max_completion_tokens=2048,
            )

            raw_response = completion.choices[0].message.content or ""
            response_text = _clean_reasoning_tags(raw_response)

            usage = completion.usage
            prompt_toks = getattr(usage, "prompt_tokens", len(prompt) // 4)
            comp_toks = getattr(usage, "completion_tokens", len(response_text) // 4)
            total_toks = getattr(usage, "total_tokens", prompt_toks + comp_toks)

            return LLMResponse(
                text=response_text,
                model_id=self.model_id,
                provider="groq_sdk",
                prompt_tokens=prompt_toks,
                completion_tokens=comp_toks,
                total_tokens=total_toks,
            )

        except AuthenticationError as e:
            logger.error(f"[GroqQwenProvider] Authentication Failed: Invalid API Key. {e}")
            fallback_text = self.offline_fallback.generate(prompt, grounding_context)
            return LLMResponse(
                text=f"{fallback_text}\n\n*(Note: Groq Auth Error — running in Grounded Fallback Mode)*",
                model_id="offline-fallback-auth-error",
                provider="groq_auth_fallback",
            )

        except RateLimitError as e:
            logger.warning(f"[GroqQwenProvider] Rate Limit Exceeded: {e}")
            fallback_text = self.offline_fallback.generate(prompt, grounding_context)
            return LLMResponse(
                text=f"{fallback_text}\n\n*(Note: Groq Rate Limit — running in Grounded Fallback Mode)*",
                model_id="offline-fallback-ratelimit",
                provider="groq_ratelimit_fallback",
            )

        except (APIConnectionError, APIStatusError, BadRequestError) as e:
            logger.warning(f"[GroqQwenProvider] Groq API Error ({type(e).__name__}): {e}")
            fallback_text = self.offline_fallback.generate(prompt, grounding_context)
            return LLMResponse(
                text=str(fallback_text),
                model_id="offline-deterministic-v1",
                provider="groq_offline_fallback",
            )

        except Exception as e:
            logger.warning(f"[GroqQwenProvider] General Exception ({type(e).__name__}): {e}")
            fallback_text = self.offline_fallback.generate(prompt, grounding_context)
            return LLMResponse(
                text=str(fallback_text),
                model_id="offline-deterministic-v1",
                provider="groq_offline_fallback",
            )
