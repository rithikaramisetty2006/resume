"""
Job matching and skill gap analysis module.
Compares candidate profiles against job descriptions.
"""

import re

from parsers.skills_db import COMMON_SKILLS, normalize_skill, find_skills_in_text


# Skill improvement suggestions mapped to common skills
SKILL_SUGGESTIONS = {
    "python": "Complete Python fundamentals on freeCodeCamp or practice on LeetCode/HackerRank.",
    "javascript": "Build small projects with vanilla JS, then explore React or Node.js tutorials.",
    "react": "Follow the official React docs and build a portfolio project with hooks and routing.",
    "java": "Study OOP principles and build a REST API with Spring Boot.",
    "sql": "Practice queries on SQLBolt or HackerRank SQL track; learn joins and indexing.",
    "aws": "Start with AWS Free Tier and pursue AWS Cloud Practitioner certification.",
    "docker": "Containerize a simple web app and learn docker-compose for multi-service setups.",
    "kubernetes": "Complete the Kubernetes basics course on Kubernetes.io after learning Docker.",
    "machine learning": "Take Andrew Ng's ML course on Coursera and implement projects with scikit-learn.",
    "data science": "Practice with pandas/numpy on Kaggle datasets and build a end-to-end analysis project.",
    "git": "Learn branching workflows and contribute to open-source projects on GitHub.",
    "flask": "Build a CRUD REST API with Flask and SQLite as a portfolio project.",
    "django": "Follow the Django official tutorial and add authentication to your project.",
    "node.js": "Build a REST API with Express and connect it to MongoDB or PostgreSQL.",
    "typescript": "Convert a JavaScript project to TypeScript and learn interfaces and generics.",
    "linux": "Set up a Linux VM and practice shell scripting and file system navigation.",
    "agile": "Read the Agile Manifesto and participate in sprint planning simulations.",
    "communication": "Practice technical writing and present project demos to improve clarity.",
    "leadership": "Lead a small team project or mentor junior developers to build leadership skills.",
}


def _skills_match(job_skill, candidate_skill):
    """Return True if job skill matches a candidate skill."""
    if not job_skill or not candidate_skill:
        return False
    if job_skill == candidate_skill:
        return True
    # Allow partial match only for skills with 3+ characters (e.g. react / react.js)
    if len(job_skill) >= 3 and len(candidate_skill) >= 3:
        return job_skill in candidate_skill or candidate_skill in job_skill
    return False


def extract_job_skills(job_description):
    """Extract required skills from a job description text."""
    # Use the same skill database to find mentioned skills
    found = find_skills_in_text(job_description)

    # Also extract skills from bullet points and comma-separated lists
    extra_skills = []
    for line in job_description.split("\n"):
        line_lower = line.lower()
        if any(kw in line_lower for kw in ["required", "must have", "qualifications", "skills"]):
            for part in re.split(r"[,;|/•\-]", line):
                part = part.strip()
                if 2 < len(part) < 40:
                    extra_skills.append(part)

    all_skills = found + extra_skills
    # Deduplicate case-insensitively
    seen = set()
    unique = []
    for s in all_skills:
        key = normalize_skill(s)
        if key not in seen:
            seen.add(key)
            unique.append(s)

    return unique


def match_candidate_to_job(candidate, job_description, job_title=""):
    """
    Match a candidate against a job description.
    Returns match score, missing skills, gap analysis, and suggestions.
    """
    candidate_skills = [normalize_skill(s) for s in candidate.get("skills", [])]
    job_skills = extract_job_skills(job_description)

    if not job_skills:
        return {
            "match_score": 0,
            "job_skills": [],
            "matched_skills": [],
            "missing_skills": [],
            "skill_gaps": [],
            "suggestions": ["Could not identify specific skills in the job description. Add clearer skill requirements."],
            "job_title": job_title,
        }

    job_skills_normalized = [normalize_skill(s) for s in job_skills]

    matched = []
    missing = []

    for orig, norm in zip(job_skills, job_skills_normalized):
        # Match skills with word-boundary awareness; avoid single-char false positives
        is_matched = any(_skills_match(norm, cs) for cs in candidate_skills)
        if is_matched:
            matched.append(orig)
        else:
            missing.append(orig)

    match_score = round((len(matched) / len(job_skills)) * 100, 1) if job_skills else 0

    # Skill gap analysis with improvement suggestions
    skill_gaps = []
    suggestions = []

    for skill in missing:
        norm = normalize_skill(skill)
        suggestion = SKILL_SUGGESTIONS.get(norm, f"Research and practice {skill} through online courses and hands-on projects.")
        gap = {
            "skill": skill,
            "priority": "high" if norm in ["python", "java", "javascript", "sql", "aws"] else "medium",
            "suggestion": suggestion,
        }
        skill_gaps.append(gap)
        suggestions.append(f"{skill}: {suggestion}")

    return {
        "match_score": match_score,
        "job_skills": job_skills,
        "matched_skills": matched,
        "missing_skills": missing,
        "skill_gaps": skill_gaps,
        "suggestions": suggestions,
        "job_title": job_title,
    }


def rank_candidates(candidates, job_description, job_title=""):
    """
    Rank multiple candidates by match score against a job description.
    Returns sorted list with match details for each candidate.
    """
    ranked = []

    for candidate in candidates:
        match_result = match_candidate_to_job(candidate, job_description, job_title)
        ranked.append({
            "candidate_id": candidate["id"],
            "full_name": candidate.get("full_name", "Unknown"),
            "email": candidate.get("email", ""),
            "match_score": match_result["match_score"],
            "matched_skills": match_result["matched_skills"],
            "missing_skills": match_result["missing_skills"],
            "completeness_score": candidate.get("completeness_score", 0),
        })

    # Sort by match score descending, then completeness as tiebreaker
    ranked.sort(key=lambda x: (x["match_score"], x["completeness_score"]), reverse=True)

    for i, item in enumerate(ranked):
        item["rank"] = i + 1

    return ranked
