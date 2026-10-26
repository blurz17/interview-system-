"""
Job Hunter Multi-Dimensional Fit Analyzer
CareerPilot Dynamic AI Engine
"""

import re
import json
import logging
from typing import Dict, Any, List, Optional
from app.integrations.llm.provider import get_llm_provider
from app.modules.job_hunter.hf_engine import JobHunterHFEngine, compute_cosine_similarity

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an expert, strict Technical Recruiter and Engineering Hiring Manager.
Evaluate the candidate's CV against the provided Job Description with high precision and strict realism.
1. Extract the REAL hard requirements directly from this specific job description (e.g., tech stack like Kafka, Airflow, Python, years of experience, spoken languages, security clearances, residency).
2. Evaluate whether the candidate's CV truly meets each requirement:
   - "Passed": CV has clear, explicit evidence of this exact skill/experience.
   - "Partial": CV has related or foundational exposure, but lacks depth or years specified.
   - "Missing": CV has no evidence of this requirement.
3. Be completely honest with the match score (0-100):
   - If core requirements are missing (e.g. required 5+ years for a student, missing Kafka/Airflow for a data role, missing German for a German-speaking role), score accordingly (e.g. 15-45%).
   - Do NOT inflate scores to 100%. A junior/student applying to a senior role missing core technologies must receive a realistic low score.
4. Check Location & Contract eligibility: identify required residency, visa sponsorship, or clearance.
5. Identify Timezone feasibility.
6. Provide actionable, tailored CV bullet points that would genuinely help bridge gaps if feasible.
7. Provide a realistic recruiter outreach pitch addressing the fit.

Output JSON strictly matching this schema:
{
  "overall_match_score": <integer 0-100>,
  "verdict": "<Strong Match | Good Match | Partial Match with Significant Gaps | Low Match / Major Disqualification>",
  "candidate_location": "<detected candidate location>",
  "location_eligible": <true or false>,
  "location_notes": "<analysis of candidate location/contract vs job requirements>",
  "timezone_eligible": <true or false>,
  "timezone_notes": "<analysis of candidate timezone/availability>",
  "hard_requirements_analysis": [
    {
      "requirement": "<Requirement extracted from job>",
      "status": "<Passed | Partial | Missing>",
      "weight": "<e.g. 20 pts>",
      "cv_evidence": "<Direct evidence from CV or explicit reason why missing>"
    }
  ],
  "bonus_points_analysis": [
    {
      "skill": "<Bonus/nice-to-have skill extracted from job>",
      "matched": <true or false>,
      "notes": "<Brief note>"
    }
  ],
  "key_strengths": ["<strength 1>", "<strength 2>"],
  "critical_gaps": ["<gap 1>", "<gap 2>"],
  "tailored_cv_bullets_to_add": ["<actionable bullet 1>", "<actionable bullet 2>"],
  "recruiter_outreach_message": "<Professional 3-paragraph outreach pitch tailored to this opening>"
}
"""


class CareerPilotJobHunterAnalyzer:
    def __init__(self, default_hf_token: Optional[str] = None):
        self.hf_engine = JobHunterHFEngine(token=default_hf_token)

    async def analyze(
        self,
        cv_text: str,
        job_info: Dict[str, Any],
        custom_hf_token: Optional[str] = None
    ) -> Dict[str, Any]:
        job_desc = job_info.get("description", "")
        job_title = job_info.get("title", "Software Engineer")
        job_company = job_info.get("company", "Employer")
        job_location = job_info.get("location", "Not specified")

        # 1. Custom Hugging Face token override if provided by user
        if custom_hf_token and custom_hf_token.strip():
            logger.info("Using custom Hugging Face token provided in request")
            hf_res = await self.hf_engine.analyze_with_hf_api(cv_text, job_desc, custom_token=custom_hf_token.strip())
            if hf_res and isinstance(hf_res, dict) and "overall_match_score" in hf_res:
                hf_res["job_meta"] = {
                    "title": job_title,
                    "company": job_company,
                    "location": job_location,
                    "url": job_info.get("url")
                }
                return hf_res

        # 2. Primary Engine: CareerPilot AI LLM Provider (Gemini / Cloud LLM)
        try:
            llm = get_llm_provider()
            user_prompt = f"""--- TARGET JOB SPECIFICATION ---
Title: {job_title}
Company: {job_company}
Location: {job_location}

{job_desc[:4500]}

--- CANDIDATE CV ---
{cv_text[:4000]}
"""
            ai_result = await llm.generate_structured(SYSTEM_PROMPT, user_prompt)
            if ai_result and isinstance(ai_result, dict) and "overall_match_score" in ai_result:
                ai_result["job_meta"] = {
                    "title": job_title,
                    "company": job_company,
                    "location": job_location,
                    "url": job_info.get("url")
                }
                ai_result["engine_used"] = f"CareerPilot AI Intelligence ({getattr(llm, 'models', ['Gemini'])[0]})"
                return ai_result
        except Exception as e:
            logger.warning(f"Primary AI generation failed, falling back to dynamic heuristic: {e}")

        # 3. Dynamic Fallback: Parse Actual Job Keywords (not static list)
        return self._dynamic_heuristic_analysis(cv_text, job_info)

    def _dynamic_heuristic_analysis(self, cv_text: str, job_info: Dict[str, Any]) -> Dict[str, Any]:
        cv_lower = cv_text.lower()
        job_desc = job_info.get("description", "")
        job_lower = job_desc.lower()
        job_title = job_info.get("title", "Software Engineer")
        job_company = job_info.get("company", "Employer")
        job_location = job_info.get("location", "Not specified")

        # Detect candidate location
        candidate_loc = "Egypt"
        for loc in ["egypt", "germany", "spain", "italy", "portugal", "poland", "greece", "uk", "usa", "france"]:
            if re.search(r'\b' + loc + r'\b', cv_lower):
                candidate_loc = loc.capitalize()
                break

        # Dynamic Technology Catalog to detect in this specific job
        TECH_CATALOG = [
            ("kafka", "Apache Kafka & Event Streaming"),
            ("airflow", "Apache Airflow & Workflow Orchestration"),
            ("spark", "Apache Spark & Distributed Processing"),
            ("trino", "Trino / Presto Distributed SQL"),
            ("nessie", "Project Nessie Data Catalog"),
            ("openshift", "Red Hat OpenShift / Kubernetes"),
            ("java", "Java Backend Development"),
            ("python", "Python Engineering"),
            ("fastapi", "FastAPI Asynchronous APIs"),
            ("django", "Django Framework"),
            ("postgresql", "PostgreSQL Database"),
            ("celery", "Celery Distributed Task Queue"),
            ("redis", "Redis In-Memory Store / Cache"),
            ("docker", "Docker Containerization"),
            ("kubernetes", "Kubernetes (K8s)"),
            ("aws", "Amazon Web Services (AWS)"),
            ("gcp", "Google Cloud Platform"),
            ("terraform", "Terraform & Infrastructure as Code"),
            ("pytest", "Automated Testing with Pytest"),
            ("german", "German Language Proficiency"),
            ("clearance", "Security Clearance (S2/NATO)"),
        ]

        # Extract requirements present in THIS job
        extracted_reqs = []
        for kw, title in TECH_CATALOG:
            if re.search(r'\b' + kw + r'\b', job_lower):
                extracted_reqs.append((kw, title))

        # Check for years of experience requirement
        exp_match = re.search(r'(\d+)\+?\s*years?', job_lower)
        if exp_match:
            years_req = exp_match.group(0)
            extracted_reqs.insert(0, ("years_exp", f"{years_req} Professional Software Experience"))

        # If no specific tech was found, default to general terms
        if not extracted_reqs:
            extracted_reqs = [
                ("python", "Python Engineering"),
                ("sql", "Relational Database & SQL"),
                ("api", "REST / HTTP APIs"),
                ("git", "Version Control & Collaboration")
            ]

        req_evals = []
        earned_score = 0
        total_weight = len(extracted_reqs) * 15

        for kw, req_title in extracted_reqs:
            weight = 15
            if kw == "years_exp":
                # Check candidate experience
                if "student" in cv_lower or "expected 2027" in cv_lower or "junior" in cv_lower:
                    status = "Missing"
                    evidence = "Candidate is currently a student / entry-level developer, lacking required professional years."
                else:
                    status = "Passed"
                    earned_score += weight
                    evidence = "Demonstrated software engineering tenure."
            else:
                has_skill = bool(re.search(r'\b' + re.escape(kw) + r'\b', cv_lower))
                if has_skill:
                    status = "Passed"
                    earned_score += weight
                    evidence = f"Candidate CV explicitly lists '{kw}'."
                else:
                    status = "Missing"
                    evidence = f"'{kw}' is required in job posting but was NOT found in candidate's CV."

            req_evals.append({
                "requirement": req_title,
                "status": status,
                "weight": f"{weight} pts",
                "cv_evidence": evidence
            })

        # Location & Clearance Check
        requires_germany = "germany" in job_lower or "german" in job_lower
        location_eligible = not (requires_germany and candidate_loc.lower() != "germany")
        if not location_eligible:
            location_notes = f"Job requires residency/clearance in Germany or EU. Candidate is located in {candidate_loc}."
        else:
            location_notes = f"Location matches ({candidate_loc})."

        base_score = int(round((earned_score / total_weight) * 100)) if total_weight > 0 else 50
        if not location_eligible:
            base_score = min(base_score, 40)

        if base_score >= 80:
            verdict = "Strong Match"
        elif base_score >= 60:
            verdict = "Good Match"
        elif base_score >= 40:
            verdict = "Partial Match with Significant Gaps"
        else:
            verdict = "Low Match / Major Disqualification"

        return {
            "overall_match_score": base_score,
            "verdict": verdict,
            "job_meta": {
                "title": job_title,
                "company": job_company,
                "location": job_location,
                "url": job_info.get("url")
            },
            "candidate_location": candidate_loc,
            "location_eligible": location_eligible,
            "location_notes": location_notes,
            "timezone_eligible": True,
            "timezone_notes": f"Candidate in {candidate_loc} (UTC+2) aligns with European collaboration hours.",
            "hard_requirements_analysis": req_evals,
            "bonus_points_analysis": [],
            "key_strengths": [r["requirement"] for r in req_evals if r["status"] == "Passed"],
            "critical_gaps": [r["requirement"] for r in req_evals if r["status"] == "Missing"],
            "tailored_cv_bullets_to_add": [
                f"Gain and document production experience with {r['requirement']}."
                for r in req_evals if r["status"] == "Missing"
            ][:4],
            "recruiter_outreach_message": f"Hi Hiring Team,\n\nI am reaching out regarding the {job_title} opening...",
            "engine_used": "CareerPilot Dynamic Heuristic Matcher"
        }
