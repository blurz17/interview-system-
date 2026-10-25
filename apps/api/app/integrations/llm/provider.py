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
    def __init__(self):
        self.api_key = settings.LLM_API_KEY
        self.model = settings.LLM_MODEL if "gemini" in settings.LLM_MODEL else "gemini-2.5-flash"
        self.timeout = settings.AI_TIMEOUT_SECONDS

    async def generate_structured(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> dict[str, Any]:
        if not self.api_key:
            return self._fallback_response(user_prompt)

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        payload = {
            "system_instruction": {"parts": [{"text": system_prompt}]},
            "contents": [{"parts": [{"text": user_prompt}]}],
            "generationConfig": {
                "response_mime_type": "application/json",
                "temperature": 0.2,
                "maxOutputTokens": settings.AI_MAX_TOKENS,
            },
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                res = await client.post(url, json=payload, headers={"Content-Type": "application/json"})
                if res.status_code == 200:
                    data = res.json()
                    parts = data["candidates"][0]["content"]["parts"]
                    text_output = parts[0]["text"].strip()
                    # Parse JSON
                    start = text_output.find("{")
                    end = text_output.rfind("}") + 1
                    if start != -1 and end != -1:
                        return json.loads(text_output[start:end])
                    return json.loads(text_output)
                logger.warning(
                    "Gemini API returned status %s: %s; using smart fallback",
                    res.status_code,
                    res.text[:200],
                )
        except Exception as e:
            logger.warning("Gemini LLM Provider error: %s; using smart fallback", str(e))

        return self._fallback_response(user_prompt)

    async def generate_text(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> str:
        if not self.api_key:
            return "Thank you for that response. Let's delve into the trade-offs and error handling."

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        payload = {
            "system_instruction": {"parts": [{"text": system_prompt}]},
            "contents": [{"parts": [{"text": user_prompt}]}],
            "generationConfig": {
                "temperature": 0.4,
                "maxOutputTokens": settings.AI_MAX_TOKENS,
            },
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                res = await client.post(url, json=payload, headers={"Content-Type": "application/json"})
                if res.status_code == 200:
                    data = res.json()
                    return data["candidates"][0]["content"]["parts"][0]["text"].strip()
                logger.warning("Gemini text generation returned status %s", res.status_code)
        except Exception as e:
            logger.warning("Gemini text generation error: %s", str(e))

        return "Thank you for that response. Could you explain the trade-offs and edge cases you would consider in production?"

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
