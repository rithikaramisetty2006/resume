/**
 * Upload page JavaScript
 * Handles file upload, drag-and-drop, parsing, and job match analysis.
 */

(function () {
    "use strict";

    // DOM Elements
    const dropZone = document.getElementById("dropZone");
    const fileInput = document.getElementById("fileInput");
    const filePreview = document.getElementById("filePreview");
    const fileName = document.getElementById("fileName");
    const clearFile = document.getElementById("clearFile");
    const uploadBtn = document.getElementById("uploadBtn");
    const loading = document.getElementById("loading");
    const errorMsg = document.getElementById("errorMsg");
    const resultsPanel = document.getElementById("resultsPanel");
    const matchBtn = document.getElementById("matchBtn");
    const downloadBtn = document.getElementById("downloadBtn");

    let selectedFile = null;
    let currentCandidate = null;

    // ---- Drag & Drop ----
    dropZone.addEventListener("click", () => fileInput.click());

    dropZone.addEventListener("dragover", (e) => {
        e.preventDefault();
        dropZone.classList.add("drag-over");
    });

    dropZone.addEventListener("dragleave", () => {
        dropZone.classList.remove("drag-over");
    });

    dropZone.addEventListener("drop", (e) => {
        e.preventDefault();
        dropZone.classList.remove("drag-over");
        if (e.dataTransfer.files.length) {
            handleFileSelect(e.dataTransfer.files[0]);
        }
    });

    fileInput.addEventListener("change", () => {
        if (fileInput.files.length) {
            handleFileSelect(fileInput.files[0]);
        }
    });

    clearFile.addEventListener("click", () => {
        selectedFile = null;
        fileInput.value = "";
        filePreview.classList.add("hidden");
        uploadBtn.disabled = true;
    });

    function handleFileSelect(file) {
        const validTypes = ["application/pdf",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"];
        const validExts = [".pdf", ".docx"];
        const ext = file.name.substring(file.name.lastIndexOf(".")).toLowerCase();

        if (!validTypes.includes(file.type) && !validExts.includes(ext)) {
            showError("Invalid file type. Please upload a PDF or DOCX file.");
            return;
        }

        if (file.size > 10 * 1024 * 1024) {
            showError("File too large. Maximum size is 10 MB.");
            return;
        }

        selectedFile = file;
        fileName.textContent = file.name;
        filePreview.classList.remove("hidden");
        uploadBtn.disabled = false;
        hideError();
    }

    // ---- Upload & Parse ----
    uploadBtn.addEventListener("click", async () => {
        if (!selectedFile) return;

        const formData = new FormData();
        formData.append("file", selectedFile);

        showLoading(true);
        hideError();
        resultsPanel.classList.add("hidden");

        try {
            const response = await fetch("/api/upload", {
                method: "POST",
                body: formData,
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || "Upload failed.");
            }

            currentCandidate = data.candidate;
            displayResults(data.candidate);
        } catch (err) {
            showError(err.message);
        } finally {
            showLoading(false);
        }
    });

    function displayResults(candidate) {
        resultsPanel.classList.remove("hidden");

        document.getElementById("resName").textContent = candidate.full_name || "—";
        document.getElementById("resEmail").textContent = candidate.email || "—";
        document.getElementById("resPhone").textContent = candidate.phone || "—";

        // Completeness badges
        const scoreBadge = document.getElementById("completenessBadge");
        scoreBadge.textContent = `Completeness: ${candidate.completeness_score}%`;

        const gradeBadge = document.getElementById("gradeBadge");
        gradeBadge.textContent = `Grade: ${candidate.completeness_grade || "N/A"}`;

        // Skills tags
        const skillsEl = document.getElementById("resSkills");
        skillsEl.innerHTML = "";
        (candidate.skills || []).forEach((skill) => {
            const tag = document.createElement("span");
            tag.className = "tag";
            tag.textContent = skill;
            skillsEl.appendChild(tag);
        });
        if (!candidate.skills || !candidate.skills.length) {
            skillsEl.innerHTML = '<span class="tag">No skills detected</span>';
        }

        // Summary
        document.getElementById("resSummary").textContent =
            candidate.professional_summary || "No summary generated.";

        // Education, Experience, Projects
        renderList("resEducation", candidate.education, "description");
        renderExperience("resExperience", candidate.experience);
        renderProjects("resProjects", candidate.projects);

        // Missing sections
        const missingPanel = document.getElementById("missingSections");
        const missingList = document.getElementById("missingList");
        missingList.innerHTML = "";

        if (candidate.missing_sections && candidate.missing_sections.length) {
            missingPanel.classList.remove("hidden");
            candidate.missing_sections.forEach((item) => {
                const li = document.createElement("li");
                li.textContent = item;
                missingList.appendChild(li);
            });
        } else {
            missingPanel.classList.add("hidden");
        }

        // Reset match results
        document.getElementById("matchResults").classList.add("hidden");
        document.getElementById("jobDescription").value = "";
        document.getElementById("jobTitle").value = "";

        resultsPanel.scrollIntoView({ behavior: "smooth" });
    }

    function renderList(elementId, items, field) {
        const el = document.getElementById(elementId);
        el.innerHTML = "";
        if (!items || !items.length) {
            el.innerHTML = "<li>No data extracted</li>";
            return;
        }
        items.forEach((item) => {
            const li = document.createElement("li");
            li.textContent = item[field] || JSON.stringify(item);
            el.appendChild(li);
        });
    }

    function renderExperience(elementId, items) {
        const el = document.getElementById(elementId);
        el.innerHTML = "";
        if (!items || !items.length) {
            el.innerHTML = "<li>No experience extracted</li>";
            return;
        }
        items.forEach((item) => {
            const li = document.createElement("li");
            li.innerHTML = `<strong>${item.title || "Role"}</strong>`;
            if (item.details && item.details.length) {
                li.innerHTML += "<br>" + item.details.slice(0, 2).join("<br>");
            }
            el.appendChild(li);
        });
    }

    function renderProjects(elementId, items) {
        const el = document.getElementById(elementId);
        el.innerHTML = "";
        if (!items || !items.length) {
            el.innerHTML = "<li>No projects extracted</li>";
            return;
        }
        items.forEach((item) => {
            const li = document.createElement("li");
            li.innerHTML = `<strong>${item.name || "Project"}</strong>`;
            if (item.details && item.details.length) {
                li.innerHTML += "<br>" + item.details[0];
            }
            el.appendChild(li);
        });
    }

    // ---- Job Match Analysis ----
    matchBtn.addEventListener("click", async () => {
        if (!currentCandidate) return;

        const jobDescription = document.getElementById("jobDescription").value.trim();
        const jobTitle = document.getElementById("jobTitle").value.trim();

        if (!jobDescription) {
            showError("Please paste a job description to analyze.");
            return;
        }

        matchBtn.disabled = true;
        matchBtn.textContent = "Analyzing…";

        try {
            const response = await fetch("/api/match", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    candidate_id: currentCandidate.id,
                    job_title: jobTitle,
                    job_description: jobDescription,
                }),
            });

            const data = await response.json();
            if (!response.ok) throw new Error(data.error);

            displayMatchResults(data.match_result);
        } catch (err) {
            showError(err.message);
        } finally {
            matchBtn.disabled = false;
            matchBtn.textContent = "Analyze Match";
        }
    });

    function displayMatchResults(result) {
        const container = document.getElementById("matchResults");
        container.classList.remove("hidden");

        let matchClass = "badge-match-low";
        if (result.match_score >= 70) matchClass = "badge-match-high";
        else if (result.match_score >= 40) matchClass = "badge-match-med";

        let html = `
            <div class="match-score-display">${result.match_score}%</div>
            <p style="text-align:center"><span class="badge ${matchClass}">Match Score</span></p>
        `;

        if (result.matched_skills && result.matched_skills.length) {
            html += `<h4>Matched Skills</h4><div class="tag-list">`;
            result.matched_skills.forEach((s) => {
                html += `<span class="tag" style="background:#d1fae5;color:#065f46">${s}</span>`;
            });
            html += `</div>`;
        }

        if (result.missing_skills && result.missing_skills.length) {
            html += `<h4 style="margin-top:1rem">Missing Skills</h4><div class="tag-list">`;
            result.missing_skills.forEach((s) => {
                html += `<span class="tag" style="background:#fee2e2;color:#991b1b">${s}</span>`;
            });
            html += `</div>`;
        }

        if (result.skill_gaps && result.skill_gaps.length) {
            html += `<h4 style="margin-top:1rem">Skill Gap Analysis</h4>`;
            result.skill_gaps.forEach((gap) => {
                html += `
                    <div class="gap-item">
                        <strong>${gap.skill} <span class="badge">${gap.priority} priority</span></strong>
                        <p>${gap.suggestion}</p>
                    </div>`;
            });
        }

        container.innerHTML = html;
    }

    // ---- Download JSON ----
    downloadBtn.addEventListener("click", () => {
        if (!currentCandidate || !currentCandidate.id) return;
        window.location.href = `/api/candidates/${currentCandidate.id}/download`;
    });

    // ---- Helpers ----
    function showLoading(show) {
        loading.classList.toggle("hidden", !show);
        uploadBtn.disabled = show;
    }

    function showError(msg) {
        errorMsg.textContent = msg;
        errorMsg.classList.remove("hidden");
    }

    function hideError() {
        errorMsg.classList.add("hidden");
    }
})();
