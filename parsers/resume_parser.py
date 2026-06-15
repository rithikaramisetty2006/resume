"""
Main resume parser module.
Orchestrates text extraction and structured data parsing from resumes.
"""

import os
import re

from parsers.pdf_parser import extract_text_from_pdf
from parsers.docx_parser import extract_text_from_docx
from parsers.skills_db import find_skills_in_text


# Regex patterns for contact information
EMAIL_PATTERN = re.compile(
    r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
)
PHONE_PATTERN = re.compile(
    r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4}"
)

# Section header keywords for parsing resume sections
SECTION_KEYWORDS = {
    "education": ["education", "academic", "qualification", "degrees", "schooling"],
    "experience": ["experience", "employment", "work history", "professional experience", "career"],
    "projects": ["projects", "personal projects", "key projects", "portfolio"],
    "skills": ["skills", "technical skills", "core competencies", "expertise", "technologies"],
}


def extract_text(file_path):
    """Extract text from PDF or DOCX based on file extension."""
    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".pdf":
        return extract_text_from_pdf(file_path)
    elif ext in (".docx", ".doc"):
        if ext == ".doc":
            raise ValueError("Legacy .doc format is not supported. Please upload .docx or .pdf")
        return extract_text_from_docx(file_path)
    else:
        raise ValueError(f"Unsupported file format: {ext}. Use PDF or DOCX.")


def extract_email(text):
    """Extract the first email address found in text."""
    match = EMAIL_PATTERN.search(text)
    return match.group(0) if match else ""


def extract_phone(text):
    """Extract the first valid phone number found in text."""
    matches = PHONE_PATTERN.findall(text)
    for match in matches:
        digits = re.sub(r"\D", "", match)
        if 7 <= len(digits) <= 15:
            return match.strip()
    return ""


def extract_name(text):
    """
    Extract candidate name using heuristics.
    Typically the first meaningful line before contact info.
    """
    lines = [line.strip() for line in text.split("\n") if line.strip()]

    for line in lines[:5]:
        # Skip lines that look like contact info or headers
        if EMAIL_PATTERN.search(line):
            continue
        if PHONE_PATTERN.search(line) and len(line) < 30:
            continue
        if any(kw in line.lower() for kw in ["resume", "curriculum vitae", "cv", "profile"]):
            continue
        # Name is usually 2-4 words, mostly alphabetic
        words = line.split()
        if 1 <= len(words) <= 5 and all(re.match(r"^[A-Za-z.\-']+$", w) for w in words):
            return line

    return lines[0] if lines else "Unknown"


def _find_section(text, section_key):
    """
    Extract content from a resume section based on header keywords.
    Returns list of bullet points or lines from that section.
    """
    keywords = SECTION_KEYWORDS.get(section_key, [])
    text_lower = text.lower()
    lines = text.split("\n")

    section_start = -1
    all_keywords = []
    for key, kws in SECTION_KEYWORDS.items():
        all_keywords.extend(kws)

    # Find where this section starts
    for i, line in enumerate(lines):
        line_lower = line.lower().strip()
        for kw in keywords:
            if line_lower == kw or line_lower.startswith(kw + ":") or line_lower.startswith(kw + " "):
                section_start = i + 1
                break
        if section_start >= 0:
            break

    if section_start < 0:
        return []

    # Collect lines until next section header
    section_lines = []
    for line in lines[section_start:]:
        stripped = line.strip()
        if not stripped:
            continue
        line_lower = stripped.lower()
        # Stop at next section header
        is_new_section = False
        for kw in all_keywords:
            if kw not in keywords and (line_lower == kw or line_lower.startswith(kw)):
                is_new_section = True
                break
        if is_new_section:
            break
        section_lines.append(stripped)

    return section_lines


def parse_education(text):
    """Parse education section into structured entries."""
    lines = _find_section(text, "education")
    if not lines:
        # Fallback: look for degree keywords anywhere
        degree_pattern = re.compile(
            r"(b\.?s\.?|b\.?a\.?|b\.?tech|m\.?s\.?|m\.?a\.?|m\.?tech|ph\.?d\.?|"
            r"bachelor|master|doctorate|diploma|b\.?e\.?|m\.?e\.?)",
            re.IGNORECASE,
        )
        for line in text.split("\n"):
            if degree_pattern.search(line):
                lines.append(line.strip())

    entries = []
    for line in lines[:10]:
        entry = {"description": line}
        # Try to extract year
        year_match = re.search(r"(19|20)\d{2}", line)
        if year_match:
            entry["year"] = year_match.group(0)
        entries.append(entry)

    return entries


def parse_experience(text):
    """Parse work experience section into structured entries."""
    lines = _find_section(text, "experience")
    entries = []
    current = None

    for line in lines:
        # Detect job title lines (often contain dates or company indicators)
        has_date = re.search(r"(19|20)\d{2}|present|current", line, re.IGNORECASE)
        is_bullet = line.startswith(("-", "•", "*", "·"))

        if has_date and not is_bullet:
            if current:
                entries.append(current)
            current = {"title": line, "details": []}
        elif current and is_bullet:
            current["details"].append(line.lstrip("-•*· ").strip())
        elif current:
            current["details"].append(line)
        elif not is_bullet:
            entries.append({"title": line, "details": []})

    if current:
        entries.append(current)

    return entries[:10]


def parse_projects(text):
    """Parse projects section into structured entries."""
    lines = _find_section(text, "projects")
    entries = []
    current = None

    for line in lines:
        is_bullet = line.startswith(("-", "•", "*", "·"))
        if not is_bullet and len(line) < 80:
            if current:
                entries.append(current)
            current = {"name": line, "details": []}
        elif current:
            current["details"].append(line.lstrip("-•*· ").strip())
        else:
            entries.append({"name": line, "details": []})

    if current:
        entries.append(current)

    return entries[:10]


def parse_resume(file_path, original_filename=None):
    """
    Main entry point: parse a resume file and return structured data.
    """
    raw_text = extract_text(file_path)

    if not raw_text or len(raw_text.strip()) < 20:
        raise ValueError("Could not extract meaningful text from the resume. The file may be scanned/image-based.")

    email = extract_email(raw_text)
    phone = extract_phone(raw_text)
    name = extract_name(raw_text)
    skills = find_skills_in_text(raw_text)

    # Also check dedicated skills section for comma-separated skills
    skills_lines = _find_section(raw_text, "skills")
    for line in skills_lines:
        for part in re.split(r"[,;|/]", line):
            part = part.strip()
            if part and 1 < len(part) < 40 and part not in skills:
                skills.append(part)

    education = parse_education(raw_text)
    experience = parse_experience(raw_text)
    projects = parse_projects(raw_text)

    return {
        "full_name": name,
        "email": email,
        "phone": phone,
        "skills": skills,
        "education": education,
        "experience": experience,
        "projects": projects,
        "raw_text": raw_text,
        "original_filename": original_filename or os.path.basename(file_path),
    }
