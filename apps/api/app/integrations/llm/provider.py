import json
import logging
from typing import Any

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class LLMProvider:
    async def generate_structured(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> dict[str, Any]:
        raise NotImplementedError


class HuggingFaceLLMProvider(LLMProvider):
    def __init__(self):
        self.api_key = settings.LLM_API_KEY
        self.model = settings.LLM_MODEL
        self.base_url = settings.LLM_API_BASE_URL
        self.timeout = settings.AI_TIMEOUT_SECONDS

    async def generate_structured(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> dict[str, Any]:
        # If no API key configured, use fallback deterministic response
        if not self.api_key:
            return self._fallback_response(user_prompt)

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "inputs": f"<|system|>\n{system_prompt}\n<|user|>\n{user_prompt}\n<|assistant|>",
            "parameters": {
                "max_new_tokens": settings.AI_MAX_TOKENS,
                "temperature": 0.2,
                "return_full_text": False,
            },
        }

        url = f"{self.base_url}/{self.model}"
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                res = await client.post(url, headers=headers, json=payload)
                if res.status_code == 200:
                    raw_text = res.json()[0]["generated_text"].strip()
                    # Parse JSON block
                    start = raw_text.find("{")
                    end = raw_text.rfind("}") + 1
                    if start != -1 and end != -1:
                        return json.loads(raw_text[start:end])
                logger.warning(
                    "HF inference returned status %s; falling back to deterministic response",
                    res.status_code,
                )
        except Exception as e:
            logger.warning("Upstream LLM provider error: %s; falling back", str(e))

        return self._fallback_response(user_prompt)

    def _fallback_response(self, user_prompt: str) -> dict[str, Any]:
        # Robust fallback response matching interviewer schema
        return {
            "message": "Thank you for sharing your thoughts. Let's dig deeper into the trade-offs or move to our next technical topic.",
            "is_follow_up": False,
            "next_action": "continue",
        }
