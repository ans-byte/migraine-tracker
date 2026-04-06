/* charts.js – Chart.js 4.x rendering for Migraine Tracker */

function isDarkMode() {
  return document.body.classList.contains("dark-mode");
}

function chartColors() {
  const dark = isDarkMode();
  return {
    grid: dark ? "rgba(255,255,255,0.08)" : "rgba(0,0,0,0.07)",
    text: dark ? "#94a3b8" : "#6c757d",
    primary: "#4f46e5",
    warning: "#f59e0b",
    success: "#10b981",
    info: "#0891b2",
    danger: "#ef4444",
  };
}

function baseOptions(yLabel, xLabel) {
  const c = chartColors();
  return {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { labels: { color: c.text, boxWidth: 12, padding: 12 } },
      tooltip: { mode: "index", intersect: false },
    },
    scales: {
      x: {
        ticks: { color: c.text, maxRotation: 45 },
        grid: { color: c.grid },
        title: xLabel ? { display: true, text: xLabel, color: c.text } : undefined,
      },
      y: {
        ticks: { color: c.text },
        grid: { color: c.grid },
        title: yLabel ? { display: true, text: yLabel, color: c.text } : undefined,
      },
    },
  };
}

/* ── Dashboard trend chart ──────────────────────────────────────────────── */
async function initDashboardChart() {
  const canvas = document.getElementById("dashboardTrendChart");
  if (!canvas) return;

  const data = await apiGet("/api/stats");
  if (!data) return;

  const trend = data.severity_trend || [];
  const labels = trend.map(d => {
    const dt = new Date(d.date + "T00:00:00");
    return dt.toLocaleDateString("en-US", { month: "short", day: "numeric" });
  });
  const severities = trend.map(d => d.severity);
  const c = chartColors();

  new Chart(canvas, {
    type: "line",
    data: {
      labels,
      datasets: [{
        label: "Severity",
        data: severities,
        borderColor: c.danger,
        backgroundColor: "rgba(239,68,68,0.12)",
        borderWidth: 2.5,
        pointBackgroundColor: c.danger,
        pointRadius: 4,
        tension: 0.35,
        fill: true,
      }],
    },
    options: {
      ...baseOptions("Severity (1–10)", "Date"),
      scales: {
        ...baseOptions("Severity (1–10)").scales,
        y: { ...baseOptions().scales?.y, min: 0, max: 10, ticks: { color: chartColors().text } },
      },
    },
  });
}

/* ── Statistics page charts ─────────────────────────────────────────────── */
async function initStatisticsCharts() {
  const data = await apiGet("/api/stats");
  if (!data) {
    console.warn("No stats data available");
    return;
  }

  // Update summary cards
  const el = id => document.getElementById(id);
  if (el("sTotalMigraines")) el("sTotalMigraines").textContent = data.total_migraines || 0;
  if (el("sAvgDuration")) el("sAvgDuration").textContent = data.avg_duration || "–";
  if (el("sTopLocation")) {
    const locs = data.location_counts || {};
    const top = Object.entries(locs).sort((a, b) => b[1] - a[1])[0];
    el("sTopLocation").textContent = top ? top[0] : "–";
  }
  if (el("sTopTrigger")) {
    const trigs = data.trigger_counts || {};
    const top = Object.entries(trigs).sort((a, b) => b[1] - a[1])[0];
    el("sTopTrigger").textContent = top ? top[0] : "–";
  }

  const c = chartColors();

  // 1. Weekly frequency bar chart
  const weeklyCanvas = document.getElementById("weeklyFreqChart");
  if (weeklyCanvas) {
    const wf = data.weekly_frequency || [];
    new Chart(weeklyCanvas, {
      type: "bar",
      data: {
        labels: wf.map(d => d.week),
        datasets: [{
          label: "Migraines",
          data: wf.map(d => d.count),
          backgroundColor: "rgba(79,70,229,0.7)",
          borderColor: c.primary,
          borderWidth: 1.5,
          borderRadius: 6,
        }],
      },
      options: {
        ...baseOptions("Count", "Week"),
        scales: { ...baseOptions().scales, y: { ticks: { stepSize: 1, color: c.text }, grid: { color: c.grid }, min: 0 } },
      },
    });
  }

  // 2. Severity trend line chart
  const sevCanvas = document.getElementById("severityTrendChart");
  if (sevCanvas) {
    const st = data.severity_trend || [];
    new Chart(sevCanvas, {
      type: "line",
      data: {
        labels: st.map(d => d.date.slice(5)),
        datasets: [{
          label: "Severity",
          data: st.map(d => d.severity),
          borderColor: c.danger,
          backgroundColor: "rgba(239,68,68,0.1)",
          borderWidth: 2.5,
          pointRadius: 4,
          tension: 0.35,
          fill: true,
        }],
      },
      options: {
        ...baseOptions("Severity (1–10)", "Date"),
        scales: { ...baseOptions().scales, y: { min: 0, max: 10, ticks: { color: c.text }, grid: { color: c.grid } } },
      },
    });
  }

  // 3. Sleep vs migraine bar chart
  const sleepCanvas = document.getElementById("sleepMigraineChart");
  if (sleepCanvas) {
    const sm = data.sleep_migraine || [];
    sm.sort((a, b) => a.date.localeCompare(b.date));
    new Chart(sleepCanvas, {
      type: "bar",
      data: {
        labels: sm.map(d => d.date.slice(5)),
        datasets: [
          {
            label: "Hours Slept",
            data: sm.map(d => d.hours),
            backgroundColor: sm.map(d => d.had_migraine ? "rgba(239,68,68,0.65)" : "rgba(8,145,178,0.65)"),
            borderColor: sm.map(d => d.had_migraine ? c.danger : c.info),
            borderWidth: 1.5,
            borderRadius: 4,
          },
        ],
      },
      options: {
        ...baseOptions("Hours", "Date"),
        plugins: {
          ...baseOptions().plugins,
          legend: { display: false },
          tooltip: {
            callbacks: {
              afterLabel: ctx => {
                const item = sm[ctx.dataIndex];
                return item && item.had_migraine ? "⚠ Migraine day" : "";
              },
            },
          },
        },
      },
    });
  }

  // 4. Triggers horizontal bar chart
  const trigsCanvas = document.getElementById("triggersChart");
  if (trigsCanvas) {
    const counts = data.trigger_counts || {};
    const sorted = Object.entries(counts).sort((a, b) => b[1] - a[1]);
    new Chart(trigsCanvas, {
      type: "bar",
      data: {
        labels: sorted.map(e => e[0]),
        datasets: [{
          label: "Occurrences",
          data: sorted.map(e => e[1]),
          backgroundColor: [
            "rgba(239,68,68,0.7)", "rgba(249,115,22,0.7)", "rgba(245,158,11,0.7)",
            "rgba(16,185,129,0.7)", "rgba(8,145,178,0.7)", "rgba(79,70,229,0.7)",
            "rgba(124,58,237,0.7)", "rgba(219,39,119,0.7)",
          ],
          borderRadius: 6,
        }],
      },
      options: {
        indexAxis: "y",
        ...baseOptions("", "Occurrences"),
        scales: {
          x: { ticks: { stepSize: 1, color: c.text }, grid: { color: c.grid }, min: 0 },
          y: { ticks: { color: c.text }, grid: { display: false } },
        },
      },
    });
  }

  // 5. Stress trend line chart
  const stressCanvas = document.getElementById("stressChart");
  if (stressCanvas) {
    const st = data.stress_trend || [];
    new Chart(stressCanvas, {
      type: "line",
      data: {
        labels: st.map(d => d.date.slice(5)),
        datasets: [{
          label: "Stress Level",
          data: st.map(d => d.level),
          borderColor: c.warning,
          backgroundColor: "rgba(245,158,11,0.12)",
          borderWidth: 2.5,
          pointRadius: 4,
          tension: 0.35,
          fill: true,
        }],
      },
      options: {
        ...baseOptions("Stress Level (1–10)", "Date"),
        scales: { ...baseOptions().scales, y: { min: 0, max: 10, ticks: { color: c.text }, grid: { color: c.grid } } },
      },
    });
  }

  // 6. Water intake area chart
  const waterCanvas = document.getElementById("waterChart");
  if (waterCanvas) {
    const wt = data.water_trend || [];
    new Chart(waterCanvas, {
      type: "line",
      data: {
        labels: wt.map(d => d.date.slice(5)),
        datasets: [{
          label: "Cups",
          data: wt.map(d => d.cups),
          borderColor: c.info,
          backgroundColor: "rgba(8,145,178,0.15)",
          borderWidth: 2.5,
          pointRadius: 4,
          tension: 0.35,
          fill: true,
        }],
      },
      options: { ...baseOptions("Cups", "Date") },
    });
  }

  // Location table
  const tbody = document.getElementById("locationTableBody");
  if (tbody) {
    const locs = data.location_counts || {};
    const total = Object.values(locs).reduce((s, v) => s + v, 0);
    if (total === 0) {
      tbody.innerHTML = '<tr><td colspan="3" class="text-muted text-center">No data</td></tr>';
    } else {
      const sorted = Object.entries(locs).sort((a, b) => b[1] - a[1]);
      tbody.innerHTML = sorted.map(([loc, cnt]) => `
        <tr>
          <td class="text-capitalize">${loc}</td>
          <td>${cnt}</td>
          <td>${Math.round((cnt / total) * 100)}%</td>
        </tr>`).join("");
    }
  }
}
