import logging
import re

from app.integrations.llm.provider import get_llm_provider
from app.models.skill import Skill

logger = logging.getLogger(__name__)


def extract_skills_regex(
    parsed_text: str,
    available_skills: list[Skill],
) -> list[tuple[Skill, str, float, str]]:
    """Heuristic fallback regex extractor for skills."""
    if not parsed_text or not available_skills:
        return []

    results = []
    lines = parsed_text.splitlines()

    current_section = "General"
    section_patterns = {
        "Skills": re.compile(r"^(skills|technical skills|technologies|proficiencies|competencies)", re.I),
        "Experience": re.compile(r"^(experience|work experience|employment|history)", re.I),
        "Projects": re.compile(r"^(projects|personal projects|academic projects)", re.I),
        "Education": re.compile(r"^(education|academics|university)", re.I),
    }

    section_lines: dict[str, list[str]] = {"General": []}
    for line in lines:
        cleaned = line.strip()
        if not cleaned:
            continue

        matched_sec = None
        for sec_name, pattern in section_patterns.items():
            if pattern.match(cleaned):
                matched_sec = sec_name
                break

        if matched_sec:
            current_section = matched_sec
            if current_section not in section_lines:
                section_lines[current_section] = []
        else:
            section_lines.setdefault(current_section, []).append(cleaned)

    for skill in available_skills:
        pattern = re.compile(rf"\b{re.escape(skill.name)}\b", re.I)
        found = False

        if "Skills" in section_lines:
            for line in section_lines["Skills"]:
                if pattern.search(line):
                    results.append((skill, line[:200], 0.95, "Skills"))
                    found = True
                    break

        if not found:
            for sec in ("Experience", "Projects"):
                if sec in section_lines:
                    for line in section_lines[sec]:
                        if pattern.search(line):
                            results.append((skill, line[:200], 0.85, sec))
                            found = True
                            break
                if found:
                    break

        if not found:
            for sec, sec_list in section_lines.items():
                if sec not in ("Skills", "Experience", "Projects"):
                    for line in sec_list:
                        if pattern.search(line):
                            results.append((skill, line[:200], 0.70, sec))
                            found = True
                            break
                if found:
                    break

    return results


async def extract_skills_from_text(
    parsed_text: str,
    available_skills: list[Skill],
) -> list[tuple[Skill, str, float, str]]:
    """AI-powered CV analysis using Gemini/LLM to extract verified skills, evidence,

    and project context, with graceful regex fallback.
    """
    if not parsed_text or not available_skills:
        return []

    llm = get_llm_provider()
    # Check if real LLM provider is active
    if hasattr(llm, "api_key") and llm.api_key:
        try:
            skill_map = {s.slug.lower(): s for s in available_skills}
            skill_names_map = {s.name.lower(): s for s in available_skills}

            skills_list_str = ", ".join([f"'{s.slug}' ({s.name})" for s in available_skills])

            system_prompt = (
                "You are an expert technical hiring manager analyzing a candidate's CV. "
                "Carefully inspect the candidate's resume text and extract the technical skills they demonstrated. "
                "Map each extracted skill ONLY to one of the provided known skill slugs. "
                "Return a strict JSON object with a 'skills' list of objects having:\n"
                "- 'slug': the matching skill slug\n"
                "- 'evidence_text': direct verbatim sentence/phrase from the CV demonstrating their usage\n"
                "- 'confidence': float between 0.70 and 1.0\n"
                "- 'source_section': name of the section (e.g., 'Experience', 'Projects', 'Skills')\n"
            )

            user_prompt = (
                f"Known Skill Catalog:\n{skills_list_str}\n\n"
                f"Candidate CV Text:\n{parsed_text[:4000]}\n\n"
                "Extract the demonstrated skills in JSON format:"
            )

            res = await llm.generate_structured(system_prompt, user_prompt)
            items = res.get("skills", [])
            if items and isinstance(items, list):
                extracted = []
                seen_slugs = set()
                for item in items:
                    slug = str(item.get("slug", "")).lower().strip()
                    skill = skill_map.get(slug) or skill_names_map.get(slug)
                    if skill and skill.slug not in seen_slugs:
                        seen_slugs.add(skill.slug)
                        snippet = str(item.get("evidence_text", "")).strip()[:300] or f"Demonstrated {skill.name} in resume."
                        conf = float(item.get("confidence", 0.90))
                        conf = max(0.60, min(1.0, conf))
                        section = str(item.get("source_section", "Experience")).strip()
                        extracted.append((skill, snippet, conf, section))

                if extracted:
                    logger.info("Successfully extracted %d skills via Gemini LLM", len(extracted))
                    return extracted
        except Exception as e:
            logger.warning("AI skill extraction failed: %s; falling back to regex", str(e))

    return extract_skills_regex(parsed_text, available_skills)
