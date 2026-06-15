/**
 * Dashboard page JavaScript
 * Loads, searches, views, ranks, and deletes candidate records.
 */

(function () {
    "use strict";

    const candidateList = document.getElementById("candidateList");
    const loading = document.getElementById("loading");
    const errorMsg = document.getElementById("errorMsg");
    const detailModal = document.getElementById("detailModal");
    const modalBody = document.getElementById("modalBody");
    const closeModal = document.getElementById("closeModal");

    // Load all candidates on page load
    document.addEventListener("DOMContentLoaded", loadCandidates);

    // Search handlers
    document.getElementById("searchBtn").addEventListener("click", searchCandidates);
    document.getElementById("clearSearchBtn").addEventListener("click", () => {
        document.getElementById("searchName").value = "";
        document.getElementById("searchSkill").value = "";
        document.getElementById("searchEducation").value = "";
        loadCandidates();
    });

    // Rank handlers
    document.getElementById("rankBtn").addEventListener("click", rankCandidates);

    // Modal close
    closeModal.addEventListener("click", () => detailModal.classList.add("hidden"));
    detailModal.addEventListener("click", (e) => {
        if (e.target === detailModal) detailModal.classList.add("hidden");
    });

    async function loadCandidates() {
        showLoading(true);
        hideError();

        try {
            const response = await fetch("/api/candidates");
            const data = await response.json();
            renderCandidates(data.candidates);
        } catch (err) {
            showError("Failed to load candidates.");
        } finally {
            showLoading(false);
        }
    }

    async function searchCandidates() {
        const name = document.getElementById("searchName").value.trim();
        const skill = document.getElementById("searchSkill").value.trim();
        const education = document.getElementById("searchEducation").value.trim();

        if (!name && !skill && !education) {
            loadCandidates();
            return;
        }

        const params = new URLSearchParams();
        if (name) params.append("name", name);
        if (skill) params.append("skill", skill);
        if (education) params.append("education", education);

        showLoading(true);
        hideError();

        try {
            const response = await fetch(`/api/candidates/search?${params}`);
            const data = await response.json();

            if (!response.ok) throw new Error(data.error);
            renderCandidates(data.candidates);
        } catch (err) {
            showError(err.message);
        } finally {
            showLoading(false);
        }
    }

    function renderCandidates(candidates) {
        candidateList.innerHTML = "";

        if (!candidates || !candidates.length) {
            candidateList.innerHTML = `
                <div class="empty-state" style="grid-column:1/-1">
                    <p>No candidates found. <a href="/">Upload a resume</a> to get started.</p>
                </div>`;
            return;
        }

        candidates.forEach((c) => {
            const card = document.createElement("div");
            card.className = "candidate-card";

            const skills = (c.skills || []).slice(0, 5);
            const skillTags = skills.map((s) => `<span class="tag">${s}</span>`).join("");

            card.innerHTML = `
                <h4>${escapeHtml(c.full_name || "Unknown")}</h4>
                <div class="meta">${escapeHtml(c.email || "No email")} · ${escapeHtml(c.phone || "No phone")}</div>
                <div class="tag-list">${skillTags || '<span class="tag">No skills</span>'}</div>
                <div style="margin-top:0.5rem">
                    <span class="badge badge-score">Completeness: ${c.completeness_score || 0}%</span>
                </div>
                <div class="card-actions">
                    <button class="btn btn-primary btn-sm" data-view="${c.id}">View Details</button>
                    <a href="/api/candidates/${c.id}/download" class="btn btn-outline btn-sm">Download JSON</a>
                    <button class="btn btn-ghost btn-sm" data-delete="${c.id}">Delete</button>
                </div>`;

            candidateList.appendChild(card);
        });

        // Event delegation for view and delete buttons
        candidateList.querySelectorAll("[data-view]").forEach((btn) => {
            btn.addEventListener("click", () => viewCandidate(btn.dataset.view));
        });

        candidateList.querySelectorAll("[data-delete]").forEach((btn) => {
            btn.addEventListener("click", () => deleteCandidate(btn.dataset.delete));
        });
    }

    async function viewCandidate(id) {
        try {
            const response = await fetch(`/api/candidates/${id}`);
            const data = await response.json();
            if (!response.ok) throw new Error(data.error);

            const c = data.candidate;
            modalBody.innerHTML = `
                <h2>${escapeHtml(c.full_name)}</h2>
                <p class="meta">${escapeHtml(c.email)} · ${escapeHtml(c.phone)}</p>
                <span class="badge badge-score">Completeness: ${c.completeness_score}%</span>
                <hr style="margin:1rem 0;border:none;border-top:1px solid var(--border)">
                <h3>Professional Summary</h3>
                <p class="summary-text">${escapeHtml(c.professional_summary || "N/A")}</p>
                <h3 style="margin-top:1rem">Skills</h3>
                <div class="tag-list">${(c.skills || []).map((s) => `<span class="tag">${escapeHtml(s)}</span>`).join("")}</div>
                <h3 style="margin-top:1rem">Education</h3>
                <ul class="detail-list">${(c.education || []).map((e) => `<li>${escapeHtml(e.description || "")}</li>`).join("") || "<li>None</li>"}</ul>
                <h3 style="margin-top:1rem">Experience</h3>
                <ul class="detail-list">${(c.experience || []).map((e) => `<li><strong>${escapeHtml(e.title || "")}</strong></li>`).join("") || "<li>None</li>"}</ul>
                <h3 style="margin-top:1rem">Projects</h3>
                <ul class="detail-list">${(c.projects || []).map((p) => `<li><strong>${escapeHtml(p.name || "")}</strong></li>`).join("") || "<li>None</li>"}</ul>`;

            detailModal.classList.remove("hidden");
        } catch (err) {
            showError(err.message);
        }
    }

    async function deleteCandidate(id) {
        if (!confirm("Are you sure you want to delete this candidate?")) return;

        try {
            const response = await fetch(`/api/candidates/${id}`, { method: "DELETE" });
            const data = await response.json();
            if (!response.ok) throw new Error(data.error);
            loadCandidates();
        } catch (err) {
            showError(err.message);
        }
    }

    async function rankCandidates() {
        const jobTitle = document.getElementById("rankJobTitle").value.trim();
        const jobDesc = document.getElementById("rankJobDesc").value.trim();

        if (!jobDesc) {
            showError("Please paste a job description to rank candidates.");
            return;
        }

        const rankBtn = document.getElementById("rankBtn");
        rankBtn.disabled = true;
        rankBtn.textContent = "Ranking…";

        try {
            const response = await fetch("/api/rank", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ job_title: jobTitle, job_description: jobDesc }),
            });

            const data = await response.json();
            if (!response.ok) throw new Error(data.error);

            displayRankResults(data.ranked_candidates);
        } catch (err) {
            showError(err.message);
        } finally {
            rankBtn.disabled = false;
            rankBtn.textContent = "Rank Candidates";
        }
    }

    function displayRankResults(ranked) {
        const container = document.getElementById("rankResults");
        container.classList.remove("hidden");

        if (!ranked.length) {
            container.innerHTML = "<p>No candidates to rank.</p>";
            return;
        }

        let html = `<h4 style="margin-bottom:0.75rem">Ranked Candidates (${ranked.length})</h4>`;

        ranked.forEach((item) => {
            let matchClass = "badge-match-low";
            if (item.match_score >= 70) matchClass = "badge-match-high";
            else if (item.match_score >= 40) matchClass = "badge-match-med";

            html += `
                <div class="rank-item">
                    <span class="rank-number">#${item.rank}</span>
                    <div style="flex:1">
                        <strong>${escapeHtml(item.full_name)}</strong>
                        <div class="meta">${escapeHtml(item.email)}</div>
                        <div class="tag-list" style="margin-top:0.25rem">
                            ${(item.matched_skills || []).map((s) => `<span class="tag">${escapeHtml(s)}</span>`).join("")}
                        </div>
                    </div>
                    <span class="badge ${matchClass}">${item.match_score}% match</span>
                </div>`;
        });

        container.innerHTML = html;
    }

    function escapeHtml(str) {
        const div = document.createElement("div");
        div.textContent = str;
        return div.innerHTML;
    }

    function showLoading(show) {
        loading.classList.toggle("hidden", !show);
    }

    function showError(msg) {
        errorMsg.textContent = msg;
        errorMsg.classList.remove("hidden");
    }

    function hideError() {
        errorMsg.classList.add("hidden");
    }
})();
