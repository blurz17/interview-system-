import re

from app.models.skill import Skill


def extract_skills_from_text(
    parsed_text: str,
    available_skills: list[Skill],
) -> list[tuple[Skill, str, float, str]]:
    """
    Extracts matching skills with evidence snippet, confidence score, and source section.
    Returns: List of (Skill, evidence_snippet, confidence, section_name)
    """
    if not parsed_text or not available_skills:
        return []

    results = []
    lines = parsed_text.splitlines()

    # Simple section detector
    current_section = "General"
    section_patterns = {
        "Skills": re.compile(
            r"^(skills|technical skills|technologies|proficiencies|competencies)", re.I
        ),
        "Experience": re.compile(r"^(experience|work experience|employment|history)", re.I),
        "Projects": re.compile(r"^(projects|personal projects|academic projects)", re.I),
        "Education": re.compile(r"^(education|academics|university)", re.I),
    }

    # Group lines by section
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

    # Search for each skill in the catalog
    for skill in available_skills:
        # Word boundary search for skill name
        pattern = re.compile(rf"\b{re.escape(skill.name)}\b", re.I)
        found = False

        # Priority 1: Check Skills section
        if "Skills" in section_lines:
            for line in section_lines["Skills"]:
                if pattern.search(line):
                    results.append((skill, line[:200], 0.95, "Skills"))
                    found = True
                    break

        # Priority 2: Check Experience & Projects
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

        # Priority 3: Check elsewhere
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
