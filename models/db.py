"""
Database module for Resume Parser.
Handles SQLite connection, schema initialization, and CRUD operations.
"""

import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime

# Path to the SQLite database file
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "resume_parser.db")
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "..", "database", "schema.sql")


def get_connection():
    """Create a database connection with row factory for dict-like access."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def db_session():
    """Context manager for database sessions with auto commit/rollback."""
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    """Initialize the database by running the schema SQL file."""
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema_sql = f.read()
    with db_session() as conn:
        conn.executescript(schema_sql)


def _row_to_dict(row):
    """Convert a sqlite3.Row to a Python dictionary with parsed JSON fields."""
    if row is None:
        return None
    data = dict(row)
    json_fields = ["skills", "education", "experience", "projects",
                   "missing_skills", "skill_gaps", "suggestions"]
    for field in json_fields:
        if field in data and isinstance(data[field], str):
            try:
                data[field] = json.loads(data[field])
            except json.JSONDecodeError:
                data[field] = []
    return data


def insert_candidate(candidate_data):
    """Insert a new parsed candidate record and return its ID."""
    with db_session() as conn:
        cursor = conn.execute(
            """
            INSERT INTO candidates (
                full_name, email, phone, skills, education, experience,
                projects, raw_text, completeness_score, professional_summary,
                original_filename
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                candidate_data.get("full_name", ""),
                candidate_data.get("email", ""),
                candidate_data.get("phone", ""),
                json.dumps(candidate_data.get("skills", [])),
                json.dumps(candidate_data.get("education", [])),
                json.dumps(candidate_data.get("experience", [])),
                json.dumps(candidate_data.get("projects", [])),
                candidate_data.get("raw_text", ""),
                candidate_data.get("completeness_score", 0),
                candidate_data.get("professional_summary", ""),
                candidate_data.get("original_filename", ""),
            ),
        )
        return cursor.lastrowid


def get_candidate(candidate_id):
    """Fetch a single candidate by ID."""
    with db_session() as conn:
        row = conn.execute(
            "SELECT * FROM candidates WHERE id = ?", (candidate_id,)
        ).fetchone()
    return _row_to_dict(row)


def get_all_candidates():
    """Fetch all candidates ordered by most recent first."""
    with db_session() as conn:
        rows = conn.execute(
            "SELECT * FROM candidates ORDER BY created_at DESC"
        ).fetchall()
    return [_row_to_dict(row) for row in rows]


def search_candidates(name=None, skill=None, education=None):
    """Search candidates by name, skill keyword, or education keyword."""
    query = "SELECT * FROM candidates WHERE 1=1"
    params = []

    if name:
        query += " AND full_name LIKE ?"
        params.append(f"%{name}%")

    if skill:
        query += " AND skills LIKE ?"
        params.append(f"%{skill}%")

    if education:
        query += " AND education LIKE ?"
        params.append(f"%{education}%")

    query += " ORDER BY created_at DESC"

    with db_session() as conn:
        rows = conn.execute(query, params).fetchall()
    return [_row_to_dict(row) for row in rows]


def delete_candidate(candidate_id):
    """Delete a candidate by ID. Returns True if a row was deleted."""
    with db_session() as conn:
        cursor = conn.execute(
            "DELETE FROM candidates WHERE id = ?", (candidate_id,)
        )
        return cursor.rowcount > 0


def insert_job_match(match_data):
    """Store a job match result for a candidate."""
    with db_session() as conn:
        cursor = conn.execute(
            """
            INSERT INTO job_matches (
                candidate_id, job_title, job_description, match_score,
                missing_skills, skill_gaps, suggestions
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                match_data["candidate_id"],
                match_data.get("job_title", ""),
                match_data.get("job_description", ""),
                match_data.get("match_score", 0),
                json.dumps(match_data.get("missing_skills", [])),
                json.dumps(match_data.get("skill_gaps", [])),
                json.dumps(match_data.get("suggestions", [])),
            ),
        )
        return cursor.lastrowid


def get_analytics():
    """Return aggregated statistics for the analytics dashboard."""
    with db_session() as conn:
        total = conn.execute("SELECT COUNT(*) FROM candidates").fetchone()[0]
        avg_completeness = conn.execute(
            "SELECT AVG(completeness_score) FROM candidates"
        ).fetchone()[0] or 0

        rows = conn.execute("SELECT skills FROM candidates").fetchall()

    # Aggregate skill frequency across all candidates
    skill_counts = {}
    for row in rows:
        try:
            skills = json.loads(row["skills"])
        except (json.JSONDecodeError, TypeError):
            skills = []
        for skill in skills:
            key = skill.strip().lower()
            if key:
                skill_counts[key] = skill_counts.get(key, 0) + 1

    top_skills = sorted(skill_counts.items(), key=lambda x: x[1], reverse=True)[:15]

    # Candidates added per month (last 6 months)
    with db_session() as conn:
        monthly = conn.execute(
            """
            SELECT strftime('%Y-%m', created_at) AS month, COUNT(*) AS count
            FROM candidates
            GROUP BY month
            ORDER BY month DESC
            LIMIT 6
            """
        ).fetchall()

    return {
        "total_candidates": total,
        "average_completeness": round(avg_completeness, 1),
        "top_skills": [{"skill": s, "count": c} for s, c in top_skills],
        "monthly_uploads": [{"month": r["month"], "count": r["count"]} for r in monthly],
        "skill_distribution": top_skills,
    }
