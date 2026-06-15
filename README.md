# Resume Parser Web Application

A full-stack resume parsing application built with **Flask**, **SQLite**, and vanilla **HTML/CSS/JavaScript**. Upload PDF or DOCX resumes, extract structured candidate data, match against job descriptions, and visualize analytics — all running locally with no paid services.

---

## Features

### Core
- Upload and parse **PDF** and **DOCX** resumes
- Extract: name, email, phone, skills, education, experience, projects
- Store parsed data in **SQLite** database
- Search candidates by name, skill, or education
- Download parsed data as **JSON**
- Responsive, modern UI

### Novelty
- **Resume Match Score** against job descriptions
- **Missing Skills Detection**
- **Skill Gap Analysis** with improvement suggestions
- **Candidate Ranking** by job requirements
- **Resume Completeness Score** (0–100 with letter grade)
- **AI-style Professional Summary** (rule-based, no API key needed)
- **Visual Analytics Dashboard** (skill distribution, monthly uploads)

---

## Project Structure

```
resume/
├── app.py                  # Main Flask app & API routes
├── requirements.txt        # Python dependencies
├── resume_parser.db        # SQLite database (auto-created on first run)
├── database/
│   └── schema.sql          # Database table definitions
├── models/
│   └── db.py               # Database connection & CRUD operations
├── parsers/
│   ├── resume_parser.py    # Main parsing orchestrator
│   ├── pdf_parser.py       # PDF text extraction (pdfplumber)
│   ├── docx_parser.py      # DOCX text extraction (python-docx)
│   └── skills_db.py        # Common skills list for matching
├── services/
│   ├── scorer.py           # Completeness score calculator
│   ├── summarizer.py       # Professional summary generator
│   └── matcher.py          # Job match, skill gap, ranking
├── static/
│   ├── css/style.css       # Global styles
│   └── js/
│       ├── app.js          # Upload page logic
│       ├── dashboard.js    # Dashboard & search logic
│       └── analytics.js    # Charts & statistics
├── templates/
│   ├── index.html          # Upload page
│   ├── dashboard.html      # Candidate dashboard
│   └── analytics.html      # Analytics page
└── uploads/                # Temporary file storage (auto-created)
```

---

## Installation

### Prerequisites
- Python 3.9 or higher
- pip (Python package manager)

### Steps

1. **Navigate to the project folder:**
   ```bash
   cd resume
   ```

2. **Create a virtual environment (recommended):**
   ```bash
   python -m venv venv

   # Windows
   venv\Scripts\activate

   # macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application:**
   ```bash
   python app.py
   ```

5. **Open in browser:**
   ```
   http://127.0.0.1:5000
   ```

The SQLite database is created automatically on first run.

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/upload` | Upload & parse a resume (multipart form, field: `file`) |
| `GET` | `/api/candidates` | List all candidates |
| `GET` | `/api/candidates/<id>` | Get single candidate |
| `GET` | `/api/candidates/search?name=&skill=&education=` | Search candidates |
| `GET` | `/api/candidates/<id>/download` | Download candidate as JSON |
| `DELETE` | `/api/candidates/<id>` | Delete a candidate |
| `POST` | `/api/match` | Match candidate to job description |
| `POST` | `/api/rank` | Rank all candidates against a job |
| `GET` | `/api/analytics` | Get analytics data |

### Example: Upload Resume
```bash
curl -X POST -F "file=@resume.pdf" http://127.0.0.1:5000/api/upload
```

### Example: Job Match
```bash
curl -X POST http://127.0.0.1:5000/api/match \
  -H "Content-Type: application/json" \
  -d '{"candidate_id": 1, "job_title": "Python Developer", "job_description": "Required: Python, Flask, SQL, Docker"}'
```

---

## Usage Guide

1. **Upload** — Go to the home page, drag & drop or browse for a PDF/DOCX resume, click "Parse Resume".
2. **Review** — View extracted details, completeness score, and professional summary.
3. **Job Match** — Paste a job description to see match score, missing skills, and improvement suggestions.
4. **Dashboard** — Browse all candidates, search by name/skill/education, rank against jobs.
5. **Analytics** — View skill distribution charts and upload statistics.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | HTML, CSS, JavaScript |
| Backend | Python Flask |
| Database | SQLite |
| PDF Parsing | pdfplumber |
| DOCX Parsing | python-docx |
| NLP/Skills | Custom regex + keyword matching |

---

## Notes

- Scanned/image-based PDFs (without selectable text) cannot be parsed. Use text-based PDFs or DOCX files.
- Legacy `.doc` format is not supported; convert to `.docx`.
- The professional summary uses rule-based generation — no external AI API required.
- Maximum upload size: **10 MB**.

---

## License

MIT — free to use for learning and personal projects.
##

updated-by rithika ramisetty
## Updates

Updated by Rithika Ramisetty
