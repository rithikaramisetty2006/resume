-- Resume Parser SQLite Database Schema
-- Run automatically on app startup via models/db.py

CREATE TABLE IF NOT EXISTS candidates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT NOT NULL DEFAULT '',
    email TEXT DEFAULT '',
    phone TEXT DEFAULT '',
    skills TEXT DEFAULT '[]',           -- JSON array
    education TEXT DEFAULT '[]',        -- JSON array of objects
    experience TEXT DEFAULT '[]',       -- JSON array of objects
    projects TEXT DEFAULT '[]',         -- JSON array of objects
    raw_text TEXT DEFAULT '',
    completeness_score REAL DEFAULT 0,
    professional_summary TEXT DEFAULT '',
    original_filename TEXT DEFAULT '',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS job_matches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    candidate_id INTEGER NOT NULL,
    job_title TEXT DEFAULT '',
    job_description TEXT DEFAULT '',
    match_score REAL DEFAULT 0,
    missing_skills TEXT DEFAULT '[]',   -- JSON array
    skill_gaps TEXT DEFAULT '[]',       -- JSON array of gap objects
    suggestions TEXT DEFAULT '[]',      -- JSON array
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (candidate_id) REFERENCES candidates(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_candidates_name ON candidates(full_name);
CREATE INDEX IF NOT EXISTS idx_candidates_email ON candidates(email);
CREATE INDEX IF NOT EXISTS idx_candidates_created ON candidates(created_at);
