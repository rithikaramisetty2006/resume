"""
Resume completeness scoring module.
Calculates how complete a parsed resume is based on key fields.
"""


def calculate_completeness_score(candidate):
    """
    Calculate a completeness score (0-100) based on presence and quality of fields.
    Each category contributes weighted points toward the total.
    """
    score = 0
    weights = {
        "full_name": 10,
        "email": 15,
        "phone": 10,
        "skills": 20,
        "education": 15,
        "experience": 20,
        "projects": 10,
    }

    if candidate.get("full_name") and candidate["full_name"] != "Unknown":
        score += weights["full_name"]

    if candidate.get("email"):
        score += weights["email"]

    if candidate.get("phone"):
        score += weights["phone"]

    skills = candidate.get("skills", [])
    if len(skills) >= 3:
        score += weights["skills"]
    elif len(skills) >= 1:
        score += weights["skills"] // 2

    education = candidate.get("education", [])
    if len(education) >= 1:
        score += weights["education"]

    experience = candidate.get("experience", [])
    if len(experience) >= 2:
        score += weights["experience"]
    elif len(experience) >= 1:
        score += weights["experience"] // 2

    projects = candidate.get("projects", [])
    if len(projects) >= 1:
        score += weights["projects"]

    # Generate feedback on missing sections
    missing = []
    if not candidate.get("email"):
        missing.append("Email address")
    if not candidate.get("phone"):
        missing.append("Phone number")
    if len(skills) < 3:
        missing.append("More skills listed")
    if not education:
        missing.append("Education section")
    if not experience:
        missing.append("Work experience")
    if not projects:
        missing.append("Projects section")

    return {
        "score": min(score, 100),
        "missing_sections": missing,
        "grade": _score_to_grade(score),
    }


def _score_to_grade(score):
    """Convert numeric score to letter grade."""
    if score >= 90:
        return "A"
    if score >= 80:
        return "B"
    if score >= 70:
        return "C"
    if score >= 60:
        return "D"
    return "F"
