"""
Hugging Face & Semantic Engine for Job Hunter
CareerPilot Backend Integration
"""

import os
import re
import math
import json
import logging
from collections import Counter
from typing import Dict, Any, List, Optional
import httpx

logger = logging.getLogger(__name__)


def tokenize(text: str) -> List[str]:
    """Extract lowercased alphanumeric tokens and bigrams."""
    words = re.findall(r"\b[a-zA-Z0-9_\+#\.-]+\b", text.lower())
    # Add bigrams
    bigrams = [f"{words[i]}_{words[i+1]}" for i in range(len(words)-1)]
    return words + bigrams


def compute_cosine_similarity(text1: str, text2: str) -> float:
    """Pure Python TF-IDF cosine similarity calculation."""
    tokens1 = tokenize(text1)
    tokens2 = tokenize(text2)
    if not tokens1 or not tokens2:
        return 0.0

    counts1 = Counter(tokens1)
    counts2 = Counter(tokens2)
    all_tokens = set(counts1.keys()).union(set(counts2.keys()))

    dot = sum(counts1.get(t, 0) * counts2.get(t, 0) for t in all_tokens)
    norm1 = math.sqrt(sum(v * v for v in counts1.values()))
    norm2 = math.sqrt(sum(v * v for v in counts2.values()))

    return (dot / (norm1 * norm2)) if (norm1 > 0 and norm2 > 0) else 0.0


class JobHunterHFEngine:
    def __init__(self, token: Optional[str] = None):
        self.token = token or os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACE_TOKEN")

    def has_token(self) -> bool:
        return bool(self.token and len(self.token.strip()) > 5)

    async def analyze_with_hf_api(
        self,
        cv_text: str,
        job_description: str,
        custom_token: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        active_token = custom_token or self.token
        if not active_token:
            return None

        prompt = f"""You are an expert Technical Recruiter and Senior Engineering Hiring Manager.
Evaluate the candidate's CV against the provided Job Description with high precision.

--- JOB DESCRIPTION ---
{job_description[:4000]}

--- CANDIDATE CV ---
{cv_text[:3500]}

Respond ONLY with a valid JSON object strictly matching this schema:
{{
    "overall_match_score": <integer 0-100>,
    "verdict": "<Strong Match | Good Match | Partial Match with Gaps | Low Match>",
    "candidate_location": "<detected candidate location>",
    "location_eligible": <true or false>,
    "location_notes": "<analysis of candidate location vs job requirements>",
    "timezone_eligible": <true or false>,
    "timezone_notes": "<analysis of candidate timezone/availability>",
    "hard_requirements_analysis": [
        {{
            "requirement": "<Requirement title>",
            "status": "<Passed | Partial | Missing>",
            "cv_evidence": "<Direct evidence from CV or explanation>",
            "weight": "<e.g. 20 pts>"
        }}
    ],
    "bonus_points_analysis": [
        {{
            "skill": "<Bonus skill title>",
            "matched": <true or false>,
            "notes": "<Brief note>"
        }}
    ],
    "key_strengths": ["<strength 1>", "<strength 2>", "<strength 3>"],
    "critical_gaps": ["<gap 1>", "<gap 2>", "<gap 3>"],
    "tailored_cv_bullets_to_add": [
        "<Action verb + technical detail + metric tailored to this job>",
        "<Action verb + technical detail + metric tailored to this job>",
        "<Action verb + technical detail + metric tailored to this job>"
    ],
    "recruiter_outreach_message": "<A 3-paragraph professional LinkedIn outreach message tailored to the hiring team>"
}}
"""
        models = [
            "meta-llama/Llama-3.1-8B-Instruct",
            "mistralai/Mistral-7B-Instruct-v0.3",
            "Qwen/Qwen2.5-72B-Instruct"
        ]

        headers = {
            "Authorization": f"Bearer {active_token}",
            "Content-Type": "application/json"
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            for model in models:
                try:
                    payload = {
                        "model": model,
                        "messages": [
                            {"role": "system", "content": "You are a specialized technical hiring analyzer. Respond ONLY with valid JSON."},
                            {"role": "user", "content": prompt}
                        ],
                        "max_tokens": 2000,
                        "temperature": 0.2
                    }
                    resp = await client.post(
                        "https://router.huggingface.co/hf-inference/v1/chat/completions",
                        headers=headers,
                        json=payload
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        raw_content = data["choices"][0]["message"]["content"].strip()
                        if raw_content.startswith("```json"):
                            raw_content = raw_content[7:]
                        if raw_content.startswith("```"):
                            raw_content = raw_content[3:]
                        if raw_content.endswith("```"):
                            raw_content = raw_content[:-3]
                        parsed = json.loads(raw_content.strip())
                        parsed["engine_used"] = f"Hugging Face Cloud LLM ({model})"
                        return parsed
                except Exception as e:
                    logger.warning(f"HF API inference failed for {model}: {e}")
                    continue

        return None
