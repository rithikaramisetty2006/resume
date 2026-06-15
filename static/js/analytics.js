/**
 * Analytics page JavaScript
 * Fetches and renders skill distribution charts and candidate statistics.
 */

(function () {
    "use strict";

    document.addEventListener("DOMContentLoaded", loadAnalytics);

    async function loadAnalytics() {
        const loading = document.getElementById("loading");
        const content = document.getElementById("analyticsContent");
        const emptyState = document.getElementById("emptyState");

        try {
            const response = await fetch("/api/analytics");
            const data = await response.json();

            loading.classList.add("hidden");

            if (data.total_candidates === 0) {
                emptyState.classList.remove("hidden");
                return;
            }

            content.classList.remove("hidden");

            // Stat cards
            document.getElementById("totalCandidates").textContent = data.total_candidates;
            document.getElementById("avgCompleteness").textContent = data.average_completeness + "%";
            document.getElementById("topSkillCount").textContent = data.top_skills.length;

            // Skills bar chart
            renderBarChart("skillsChart", data.top_skills, "skill", "count");

            // Monthly uploads chart
            const monthly = (data.monthly_uploads || []).reverse();
            renderBarChart(
                "monthlyChart",
                monthly.map((m) => ({ label: m.month, value: m.count })),
                "label",
                "value"
            );

            // Skills table
            renderSkillsTable(data.top_skills);
        } catch (err) {
            loading.classList.add("hidden");
            emptyState.classList.remove("hidden");
            emptyState.innerHTML = `<p>Failed to load analytics. ${err.message}</p>`;
        }
    }

    function renderBarChart(containerId, items, labelKey, valueKey) {
        const container = document.getElementById(containerId);
        container.innerHTML = "";

        if (!items || !items.length) {
            container.innerHTML = "<p style='color:var(--text-muted)'>No data available</p>";
            return;
        }

        const maxVal = Math.max(...items.map((i) => i[valueKey] || i.count || 0));

        items.forEach((item) => {
            const label = item[labelKey] || item.skill || item.label || "";
            const value = item[valueKey] || item.count || item.value || 0;
            const pct = maxVal > 0 ? (value / maxVal) * 100 : 0;

            const row = document.createElement("div");
            row.className = "bar-row";
            row.innerHTML = `
                <span class="bar-label" title="${label}">${label}</span>
                <div class="bar-track">
                    <div class="bar-fill" style="width:${pct}%">
                        <span>${value}</span>
                    </div>
                </div>`;
            container.appendChild(row);
        });
    }

    function renderSkillsTable(skills) {
        const tbody = document.querySelector("#skillsTable tbody");
        tbody.innerHTML = "";

        if (!skills || !skills.length) {
            tbody.innerHTML = "<tr><td colspan='4'>No skills data</td></tr>";
            return;
        }

        const maxCount = Math.max(...skills.map((s) => s.count));

        skills.forEach((item, index) => {
            const pct = maxCount > 0 ? (item.count / maxCount) * 100 : 0;
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td>${index + 1}</td>
                <td>${item.skill}</td>
                <td>${item.count}</td>
                <td><div class="table-bar" style="width:${pct}%"></div></td>`;
            tbody.appendChild(tr);
        });
    }
})();
