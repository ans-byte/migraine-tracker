/* ── Dark/light mode ──────────────────────────────────────────────────── */
(function () {
  const saved = localStorage.getItem("theme");
  if (saved === "dark") document.body.classList.add("dark-mode");
})();

document.addEventListener("DOMContentLoaded", () => {
  const btn = document.getElementById("themeToggle");
  const icon = document.getElementById("themeIcon");
  if (!btn) return;

  function applyTheme(dark) {
    document.body.classList.toggle("dark-mode", dark);
    icon.className = dark ? "bi bi-sun-fill" : "bi bi-moon-fill";
    localStorage.setItem("theme", dark ? "dark" : "light");
  }

  applyTheme(document.body.classList.contains("dark-mode"));

  btn.addEventListener("click", () => {
    applyTheme(!document.body.classList.contains("dark-mode"));
  });
});

/* ── AJAX helper ──────────────────────────────────────────────────────── */
async function apiPost(url, data) {
  try {
    const res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    return await res.json();
  } catch (err) {
    console.error("API error:", err);
    return { error: "Network error. Please try again." };
  }
}

async function apiGet(url) {
  try {
    const res = await fetch(url);
    return await res.json();
  } catch (err) {
    console.error("API error:", err);
    return null;
  }
}

/* ── Toast notifications ──────────────────────────────────────────────── */
function showToast(message, type = "success") {
  const container = document.getElementById("toastContainer");
  if (!container) return;
  const id = "toast-" + Date.now();
  const iconMap = {
    success: "bi-check-circle-fill",
    danger: "bi-x-circle-fill",
    warning: "bi-exclamation-triangle-fill",
    info: "bi-info-circle-fill",
  };
  const colorMap = {
    success: "text-bg-success",
    danger: "text-bg-danger",
    warning: "text-bg-warning",
    info: "text-bg-info",
  };
  const html = `
    <div id="${id}" class="toast align-items-center ${colorMap[type] || "text-bg-secondary"} border-0 show" role="alert">
      <div class="d-flex">
        <div class="toast-body fw-semibold">
          <i class="bi ${iconMap[type] || "bi-info-circle"} me-2"></i>${message}
        </div>
        <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
      </div>
    </div>`;
  container.insertAdjacentHTML("beforeend", html);
  setTimeout(() => {
    const el = document.getElementById(id);
    if (el) el.remove();
  }, 4000);
}

/* ── Severity badge ───────────────────────────────────────────────────── */
function updateSeverityBadge(value) {
  const badge = document.getElementById("severityBadge");
  if (!badge) return;
  badge.textContent = value;
  badge.className = "badge severity-badge ms-2 severity-" + value;
}

/* ── Stress badge ─────────────────────────────────────────────────────── */
function updateStressBadge(value) {
  const badge = document.getElementById("stressBadge");
  if (!badge) return;
  badge.textContent = value;
  const sev = value <= 3 ? 2 : value <= 6 ? 5 : value <= 8 ? 7 : 10;
  badge.className = "badge severity-badge ms-2 severity-" + sev;
}

/* ── Delete migraine ──────────────────────────────────────────────────── */
async function deleteMigraine(id) {
  if (!confirm("Delete this migraine entry?")) return;
  try {
    const res = await fetch(`/api/migraine/${id}`, { method: "DELETE" });
    const data = await res.json();
    if (data.success) {
      showToast("Entry deleted", "success");
      setTimeout(() => location.reload(), 800);
    } else {
      showToast(data.error || "Failed to delete", "danger");
    }
  } catch (err) {
    showToast("Network error", "danger");
  }
}

/* ── Recent activity ──────────────────────────────────────────────────── */
async function loadRecentActivity() {
  const container = document.getElementById("recentActivity");
  if (!container) return;

  const items = await apiGet("/api/recent");
  if (!items || items.length === 0) {
    container.innerHTML = '<li class="list-group-item text-muted text-center py-3">No recent activity</li>';
    return;
  }

  const iconMap = {
    migraine: { icon: "bi-activity", cls: "activity-migraine" },
    sleep:    { icon: "bi-moon-stars", cls: "activity-sleep" },
    water:    { icon: "bi-droplet", cls: "activity-water" },
    stress:   { icon: "bi-lightning", cls: "activity-stress" },
  };

  container.innerHTML = items.slice(0, 10).map(item => {
    const cfg = iconMap[item.type] || { icon: "bi-circle", cls: "" };
    const d = new Date(item.date + "T00:00:00");
    const dateStr = d.toLocaleDateString("en-US", { month: "short", day: "numeric" });
    return `
      <li class="list-group-item d-flex align-items-center gap-3 py-2">
        <div class="activity-icon ${cfg.cls}"><i class="bi ${cfg.icon}"></i></div>
        <div class="flex-grow-1">
          <div class="fw-semibold small">${item.label}</div>
          <div class="text-muted" style="font-size:0.75rem">${dateStr}</div>
        </div>
      </li>`;
  }).join("");
}

/* ── Mini calendar ────────────────────────────────────────────────────── */
async function renderMiniCalendar() {
  const container = document.getElementById("miniCalendar");
  if (!container) return;

  const calData = await apiGet("/api/calendar-data");
  const migraineByDate = {};
  if (calData) {
    calData.forEach(m => { migraineByDate[m.date] = m.severity; });
  }

  const now = new Date();
  const year = now.getFullYear();
  const month = now.getMonth();
  const today = now.getDate();
  const firstDay = new Date(year, month, 1).getDay();
  const daysInMonth = new Date(year, month + 1, 0).getDate();

  const dayNames = ["Su","Mo","Tu","We","Th","Fr","Sa"];
  let html = `<div class="cal-header">${dayNames.map(d => `<div>${d}</div>`).join("")}</div>`;
  html += '<div class="cal-grid">';
  for (let i = 0; i < firstDay; i++) html += '<div class="cal-cell empty"></div>';
  for (let d = 1; d <= daysInMonth; d++) {
    const isoDate = `${year}-${String(month+1).padStart(2,"0")}-${String(d).padStart(2,"0")}`;
    const sev = migraineByDate[isoDate];
    let cls = "cal-cell";
    if (d === today) cls += " today";
    if (sev) cls += ` migraine-${sev}`;
    const title = sev ? `Migraine (severity ${sev})` : "";
    html += `<div class="${cls}" title="${title}">${d}</div>`;
  }
  html += "</div>";
  container.innerHTML = html;
}
