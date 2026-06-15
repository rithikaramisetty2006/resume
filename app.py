"""
Resume Parser - Main Flask Application
Provides web UI and REST API for resume parsing, storage, and job matching.
"""

import json
import os
import uuid
from flask import Flask, render_template, request, jsonify, send_file
from werkzeug.utils import secure_filename

from models import db
from parsers.resume_parser import parse_resume
from services.scorer import calculate_completeness_score
from services.summarizer import generate_professional_summary
from services.matcher import match_candidate_to_job, rank_candidates

# ---------------------------------------------------------------------------
# App Configuration
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
ALLOWED_EXTENSIONS = {"pdf", "docx"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = MAX_FILE_SIZE
app.secret_key = os.environ.get("SECRET_KEY", "resume-parser-dev-key-change-in-production")

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialize database on startup
db.init_db()


def allowed_file(filename):
    """Check if uploaded file has an allowed extension."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# ---------------------------------------------------------------------------
# Web Pages (HTML routes)
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    """Upload page — main entry point."""
    return render_template("index.html")


@app.route("/dashboard")
def dashboard():
    """Candidate dashboard — view and search parsed resumes."""
    return render_template("dashboard.html")


@app.route("/analytics")
def analytics_page():
    """Analytics dashboard — skill distribution and statistics."""
    return render_template("analytics.html")


# ---------------------------------------------------------------------------
# API Endpoints
# ---------------------------------------------------------------------------

@app.route("/api/upload", methods=["POST"])
def upload_resume():
    """
    Upload and parse a resume file (PDF or DOCX).
    Returns parsed data with completeness score and professional summary.
    """
    if "file" not in request.files:
        return jsonify({"error": "No file provided. Please select a resume file."}), 400

    file = request.files["file"]

    if file.filename == "" or file.filename is None:
        return jsonify({"error": "No file selected."}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": "Invalid file type. Only PDF and DOCX files are allowed."}), 400

    # Save uploaded file with unique name to avoid collisions
    original_name = secure_filename(file.filename)
    ext = original_name.rsplit(".", 1)[1].lower()
    unique_name = f"{uuid.uuid4().hex}.{ext}"
    file_path = os.path.join(app.config["UPLOAD_FOLDER"], unique_name)

    try:
        file.save(file_path)

        # Parse the resume
        parsed = parse_resume(file_path, original_filename=original_name)

        # Calculate completeness score
        completeness = calculate_completeness_score(parsed)
        parsed["completeness_score"] = completeness["score"]
        parsed["completeness_grade"] = completeness["grade"]
        parsed["missing_sections"] = completeness["missing_sections"]

        # Generate professional summary
        parsed["professional_summary"] = generate_professional_summary(parsed)

        # Store in database
        candidate_id = db.insert_candidate(parsed)
        parsed["id"] = candidate_id

        return jsonify({
            "success": True,
            "message": "Resume parsed successfully.",
            "candidate": parsed,
        }), 201

    except ValueError as e:
        return jsonify({"error": str(e)}), 422
    except Exception as e:
        return jsonify({"error": f"Failed to parse resume: {str(e)}"}), 500
    finally:
        # Clean up uploaded file after processing
        if os.path.exists(file_path):
            os.remove(file_path)


@app.route("/api/candidates", methods=["GET"])
def list_candidates():
    """Get all parsed candidates."""
    candidates = db.get_all_candidates()
    return jsonify({"candidates": candidates, "count": len(candidates)})


@app.route("/api/candidates/<int:candidate_id>", methods=["GET"])
def get_candidate(candidate_id):
    """Get a single candidate by ID."""
    candidate = db.get_candidate(candidate_id)
    if not candidate:
        return jsonify({"error": "Candidate not found."}), 404
    return jsonify({"candidate": candidate})


@app.route("/api/candidates/search", methods=["GET"])
def search_candidates():
    """
    Search candidates by name, skill, or education keyword.
    Query params: name, skill, education
    """
    name = request.args.get("name", "").strip()
    skill = request.args.get("skill", "").strip()
    education = request.args.get("education", "").strip()

    if not any([name, skill, education]):
        return jsonify({"error": "Provide at least one search parameter: name, skill, or education."}), 400

    results = db.search_candidates(name=name or None, skill=skill or None, education=education or None)
    return jsonify({"candidates": results, "count": len(results)})


@app.route("/api/candidates/<int:candidate_id>/download", methods=["GET"])
def download_candidate_json(candidate_id):
    """Download parsed candidate data as a JSON file."""
    candidate = db.get_candidate(candidate_id)
    if not candidate:
        return jsonify({"error": "Candidate not found."}), 404

    # Remove raw_text from download to keep file size manageable (optional)
    export_data = {k: v for k, v in candidate.items() if k != "raw_text"}

    # Write to temp file
    export_path = os.path.join(app.config["UPLOAD_FOLDER"], f"candidate_{candidate_id}.json")
    with open(export_path, "w", encoding="utf-8") as f:
        json.dump(export_data, f, indent=2, ensure_ascii=False)

    filename = f"{candidate.get('full_name', 'candidate').replace(' ', '_')}_resume.json"

    return send_file(
        export_path,
        as_attachment=True,
        download_name=filename,
        mimetype="application/json",
    )


@app.route("/api/candidates/<int:candidate_id>", methods=["DELETE"])
def delete_candidate(candidate_id):
    """Delete a candidate record."""
    if db.delete_candidate(candidate_id):
        return jsonify({"success": True, "message": "Candidate deleted."})
    return jsonify({"error": "Candidate not found."}), 404


@app.route("/api/match", methods=["POST"])
def match_job():
    """
    Match a candidate against a job description.
    Body JSON: { candidate_id, job_title, job_description }
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body must be JSON."}), 400

    candidate_id = data.get("candidate_id")
    job_description = data.get("job_description", "").strip()
    job_title = data.get("job_title", "").strip()

    if not candidate_id:
        return jsonify({"error": "candidate_id is required."}), 400
    if not job_description:
        return jsonify({"error": "job_description is required."}), 400

    candidate = db.get_candidate(candidate_id)
    if not candidate:
        return jsonify({"error": "Candidate not found."}), 404

    result = match_candidate_to_job(candidate, job_description, job_title)

    # Store match result in database
    db.insert_job_match({
        "candidate_id": candidate_id,
        "job_title": job_title,
        "job_description": job_description,
        **result,
    })

    return jsonify({
        "success": True,
        "candidate_name": candidate.get("full_name"),
        "match_result": result,
    })


@app.route("/api/rank", methods=["POST"])
def rank_candidates_api():
    """
    Rank all candidates against a job description.
    Body JSON: { job_title, job_description }
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body must be JSON."}), 400

    job_description = data.get("job_description", "").strip()
    job_title = data.get("job_title", "").strip()

    if not job_description:
        return jsonify({"error": "job_description is required."}), 400

    candidates = db.get_all_candidates()
    if not candidates:
        return jsonify({"error": "No candidates in database."}), 404

    ranked = rank_candidates(candidates, job_description, job_title)

    return jsonify({
        "success": True,
        "job_title": job_title,
        "ranked_candidates": ranked,
        "total": len(ranked),
    })


@app.route("/api/analytics", methods=["GET"])
def analytics_api():
    """Return analytics data for the dashboard charts."""
    return jsonify(db.get_analytics())


# ---------------------------------------------------------------------------
# Error Handlers
# ---------------------------------------------------------------------------

@app.errorhandler(413)
def file_too_large(e):
    return jsonify({"error": "File too large. Maximum size is 10 MB."}), 413


@app.errorhandler(404)
def not_found(e):
    if request.path.startswith("/api/"):
        return jsonify({"error": "Endpoint not found."}), 404
    return render_template("index.html"), 404


@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "Internal server error."}), 500


# ---------------------------------------------------------------------------
# Run Application
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 50)
    print("  Resume Parser Application")
    print("  Open http://127.0.0.1:5000 in your browser")
    print("=" * 50)
    app.run(debug=True, host="127.0.0.1", port=5000)
