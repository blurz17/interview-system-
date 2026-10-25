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

    async def generate_text(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> str:
        raise NotImplementedError


class GeminiLLMProvider(LLMProvider):
    MODELS_TO_TRY = ["gemini-flash-lite-latest", "gemini-flash-latest", "gemma-4-26b-a4b-it"]

    def __init__(self):
        self.api_key = settings.LLM_API_KEY
        configured_model = settings.LLM_MODEL or "gemini-flash-lite-latest"
        # Put configured model first, followed by alternates
        self.models = [configured_model] + [m for m in self.MODELS_TO_TRY if m != configured_model]
        self.timeout = settings.AI_TIMEOUT_SECONDS

    async def generate_structured(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> dict[str, Any]:
        if not self.api_key:
            return self._fallback_response(user_prompt)

        payload = {
            "system_instruction": {"parts": [{"text": system_prompt}]},
            "contents": [{"parts": [{"text": user_prompt}]}],
            "generationConfig": {
                "response_mime_type": "application/json",
                "temperature": 0.2,
                "maxOutputTokens": settings.AI_MAX_TOKENS,
            },
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for model in self.models:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.api_key}"
                try:
                    res = await client.post(url, json=payload, headers={"Content-Type": "application/json"})
                    if res.status_code == 200:
                        data = res.json()
                        parts = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])
                        text_output = parts[0].get("text", "").strip()
                        start = text_output.find("{")
                        end = text_output.rfind("}") + 1
                        if start != -1 and end != -1:
                            return json.loads(text_output[start:end])
                        return json.loads(text_output)
                    logger.warning(
                        "Gemini model %s returned status %s: %s; trying next model",
                        model,
                        res.status_code,
                        res.text[:150],
                    )
                except Exception as e:
                    logger.warning("Gemini error with model %s: %s", model, str(e))

        return self._fallback_response(user_prompt)

    async def generate_text(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> str:
        if not self.api_key:
            return self._dynamic_text_fallback(user_prompt)

        payload = {
            "system_instruction": {"parts": [{"text": system_prompt}]},
            "contents": [{"parts": [{"text": user_prompt}]}],
            "generationConfig": {
                "temperature": 0.6,
                "maxOutputTokens": settings.AI_MAX_TOKENS,
            },
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for model in self.models:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.api_key}"
                try:
                    res = await client.post(url, json=payload, headers={"Content-Type": "application/json"})
                    if res.status_code == 200:
                        data = res.json()
                        parts = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])
                        text = parts[0].get("text", "").strip()
                        if text:
                            return text
                    logger.warning("Gemini text gen (%s) returned %s: %s", model, res.status_code, res.text[:150])
                except Exception as e:
                    logger.warning("Gemini text gen error (%s): %s", model, str(e))

        return self._dynamic_text_fallback(user_prompt)

    def _dynamic_text_fallback(self, user_prompt: str) -> str:
        prompt_lower = user_prompt.lower()
        if "question 1" in prompt_lower or "question #1" in prompt_lower or "opening" in prompt_lower:
            return (
                "Hello and welcome to your technical interview! We will dive into real-world architecture, trade-offs, and design decisions. "
                "To start: In a distributed system with high write volume, how would you approach database partitioning or sharding, and how do you handle cross-shard transactions?"
            )
        if len(user_prompt.strip()) < 30 or "latest answer:\n\"n\"" in prompt_lower or "latest answer:\n\"\"" in prompt_lower:
            return (
                "It looks like your response was very brief. Could you expand a bit on your reasoning or outline how you would address the core trade-offs in this scenario?"
            )
        if "scale" in prompt_lower or "bottleneck" in prompt_lower:
            return (
                "That provides helpful context. Let's dig deeper: What happens when the message broker or queue experiences backpressure under sudden 10x traffic spikes?"
            )
        return (
            "Good points on the trade-offs. Let's explore fault tolerance: If a critical downstream dependency starts returning 500 errors or high latency, how would you design a circuit breaker and fallback strategy?"
        )

    def _fallback_response(self, user_prompt: str) -> dict[str, Any]:
        return {
            "message": "Thank you for that structured explanation. Can you elaborate on the performance characteristics, failure modes, and potential bottleneck in that design?",
            "is_follow_up": True,
            "next_action": "continue",
        }


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
                    start = raw_text.find("{")
                    end = raw_text.rfind("}") + 1
                    if start != -1 and end != -1:
                        return json.loads(raw_text[start:end])
                logger.warning("HF inference returned status %s", res.status_code)
        except Exception as e:
            logger.warning("HF LLM error: %s", str(e))

        return self._fallback_response(user_prompt)

    async def generate_text(self, system_prompt: str, user_prompt: str) -> str:
        res = await self.generate_structured(system_prompt, user_prompt)
        return res.get("message", "Let's explore your architectural choices.")

    def _fallback_response(self, user_prompt: str) -> dict[str, Any]:
        return {
            "message": "Thank you for sharing your thoughts. Let's dig deeper into the trade-offs or move to our next technical topic.",
            "is_follow_up": False,
            "next_action": "continue",
        }


def get_llm_provider() -> LLMProvider:
    if settings.LLM_PROVIDER == "gemini" or settings.LLM_API_KEY.startswith("AQ.") or settings.LLM_API_KEY.startswith("AIza"):
        return GeminiLLMProvider()
    return HuggingFaceLLMProvider()
