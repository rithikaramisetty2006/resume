"""
Common skills database and skill-related utilities.
Used for skill extraction and job matching.
"""

import re

# Curated list of common technical and soft skills for matching
COMMON_SKILLS = [
    # Programming Languages
    "python", "java", "javascript", "typescript", "c++", "c#", "c", "go", "golang",
    "rust", "ruby", "php", "swift", "kotlin", "scala", "r", "matlab", "perl",
    # Web Technologies
    "html", "css", "react", "angular", "vue", "vue.js", "node.js", "nodejs",
    "express", "django", "flask", "fastapi", "spring", "spring boot", ".net",
    "asp.net", "next.js", "nextjs", "graphql", "rest api", "restful",
    # Databases
    "sql", "mysql", "postgresql", "postgres", "mongodb", "redis", "sqlite",
    "oracle", "dynamodb", "firebase", "elasticsearch", "cassandra",
    # Cloud & DevOps
    "aws", "azure", "gcp", "google cloud", "docker", "kubernetes", "k8s",
    "jenkins", "ci/cd", "terraform", "ansible", "linux", "git", "github",
    "gitlab", "devops", "microservices",
    # Data & ML
    "machine learning", "deep learning", "tensorflow", "pytorch", "keras",
    "scikit-learn", "pandas", "numpy", "data analysis", "data science",
    "nlp", "natural language processing", "computer vision", "statistics",
    "tableau", "power bi", "spark", "hadoop", "etl",
    # Mobile
    "android", "ios", "react native", "flutter",
    # Tools & Other
    "agile", "scrum", "jira", "figma", "photoshop", "excel", "powerpoint",
    "communication", "leadership", "problem solving", "teamwork",
    "project management", "testing", "selenium", "junit", "api",
    "object-oriented programming", "oop", "design patterns",
    "microservices", "blockchain", "cybersecurity", "networking",
]


def normalize_skill(skill):
    """Normalize a skill string for comparison."""
    return skill.strip().lower()


def find_skills_in_text(text):
    """
    Find known skills mentioned in resume text.
    Returns a deduplicated list preserving original casing where found.
    """
    text_lower = text.lower()
    found = []
    seen = set()

    for skill in COMMON_SKILLS:
        if skill in seen:
            continue
        # Use word-boundary matching to avoid false positives (e.g. "c" in "react")
        if len(skill) <= 2:
            pattern = re.compile(r"(?<![a-z0-9])" + re.escape(skill) + r"(?![a-z0-9])")
            matched = bool(pattern.search(text_lower))
        else:
            matched = skill in text_lower

        if matched:
            seen.add(skill)
            found.append(skill.title() if len(skill) > 3 else skill.upper())

    return sorted(found, key=str.lower)
