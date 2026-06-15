"""
Professional summary generator.
Creates an AI-style summary from extracted resume data (rule-based, no external API).
"""


def generate_professional_summary(candidate):
    """
    Generate a professional summary paragraph from parsed candidate data.
    Uses template-based natural language generation — no paid API required.
    """
    name = candidate.get("full_name", "The candidate")
    skills = candidate.get("skills", [])
    experience = candidate.get("experience", [])
    education = candidate.get("education", [])
    projects = candidate.get("projects", [])

    parts = []

    # Opening line based on experience level
    exp_count = len(experience)
    if exp_count >= 3:
        parts.append(f"{name} is an experienced professional with a strong background across multiple roles.")
    elif exp_count >= 1:
        parts.append(f"{name} is a motivated professional with demonstrated experience in their field.")
    else:
        parts.append(f"{name} is an emerging professional eager to apply their skills and knowledge.")

    # Skills summary
    if skills:
        top_skills = skills[:6]
        skill_str = ", ".join(top_skills[:-1]) + f", and {top_skills[-1]}" if len(top_skills) > 1 else top_skills[0]
        parts.append(f"They possess expertise in {skill_str}.")

    # Experience highlight
    if experience:
        latest = experience[0]
        title = latest.get("title", "")
        if title:
            parts.append(f"Their most recent role includes: {title[:120]}.")

    # Education highlight
    if education:
        edu_desc = education[0].get("description", "")
        if edu_desc:
            parts.append(f"Educational background: {edu_desc[:120]}.")

    # Projects highlight
    if projects:
        project_names = [p.get("name", "") for p in projects[:2] if p.get("name")]
        if project_names:
            parts.append(f"Notable projects include {', '.join(project_names)}.")

    # Closing
    parts.append("They bring a combination of technical skills and practical experience suitable for challenging roles.")

    return " ".join(parts)
