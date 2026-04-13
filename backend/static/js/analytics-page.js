/**
 * Аналитика Turnpike: демо-графики (Chart.js), тепловая карта, журнал операций.
 */
(function () {
  function padZero(n) {
    return String(n).padStart(2, "0");
  }

  function fmtShort(d) {
    return padZero(d.getDate()) + "." + padZero(d.getMonth() + 1);
  }

  function demoDate(dayOffset, hour, min) {
    const d = new Date();
    d.setDate(d.getDate() - dayOffset);
    d.setHours(hour, min, 0, 0);
    return (
      padZero(d.getDate()) +
      "." +
      padZero(d.getMonth() + 1) +
      " " +
      padZero(d.getHours()) +
      ":" +
      padZero(d.getMinutes())
    );
  }

  const OPERATIONS_LOG = [
    {
      time: demoDate(0, 9, 12),
      action: "Синхронизация",
      detail: "Справочник «Партнёры»",
      source: "API Аксиома24",
      duration: "0.8 с",
      color: "#14b8a6",
    },
    {
      time: demoDate(0, 8, 44),
      action: "Экспорт",
      detail: "Контакты (CSV)",
      source: "Веб-приложение",
      duration: "2.1 с",
      color: "#3b82f6",
    },
    {
      time: demoDate(1, 16, 30),
      action: "Обновление",
      detail: "Регионы и города",
      source: "API Аксиома24",
      duration: "1.4 с",
      color: "#14b8a6",
    },
    {
      time: demoDate(1, 11, 5),
      action: "Просмотр",
      detail: "Поток камеры",
      source: "Камеры",
      duration: "—",
      color: "#f59e0b",
    },
    {
      time: demoDate(2, 14, 22),
      action: "Сессия",
      detail: "Вход пользователя",
      source: "Авторизация",
      duration: "—",
      color: "#94a3b8",
    },
  ];

  function renderHeatmap() {
    const el = document.getElementById("analyticsHeatmap");
    if (!el) return;

    const dayNames = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"];
    const pattern = [
      [1, 0, 0, 0, 0, 1, 2, 5, 7, 4, 2, 2, 3, 4, 2, 2, 3, 5, 6, 5, 3, 2, 1, 1],
      [0, 0, 1, 0, 0, 0, 2, 6, 8, 3, 2, 1, 3, 3, 2, 2, 3, 6, 7, 4, 3, 2, 1, 0],
      [1, 0, 0, 0, 0, 0, 1, 5, 6, 4, 2, 2, 2, 3, 2, 1, 2, 5, 6, 4, 3, 2, 1, 1],
      [0, 0, 0, 1, 0, 0, 2, 6, 7, 3, 2, 1, 3, 4, 2, 2, 3, 7, 8, 5, 3, 2, 1, 0],
      [1, 0, 0, 0, 0, 1, 2, 5, 7, 3, 2, 2, 2, 3, 2, 2, 4, 6, 7, 5, 4, 3, 2, 1],
      [0, 1, 0, 0, 0, 0, 0, 1, 2, 3, 4, 4, 5, 4, 3, 3, 3, 4, 5, 4, 3, 2, 1, 1],
      [0, 0, 0, 0, 0, 0, 0, 1, 1, 2, 3, 3, 4, 3, 2, 2, 3, 4, 5, 4, 3, 2, 1, 0],
    ];

    const emptyBg = "#334155";
    let html = "<div></div>";
    for (let h = 0; h < 24; h++) {
      html += '<div class="analytics-heatmap-hour">' + padZero(h) + "</div>";
    }
    for (let d = 0; d < 7; d++) {
      html += '<div class="analytics-heatmap-label">' + dayNames[d] + "</div>";
      for (let h = 0; h < 24; h++) {
        const v = pattern[d][h];
        const max = 8;
        const intensity = v / max;
        const bg =
          intensity === 0
            ? emptyBg
            : "rgba(20, 184, 166, " + (0.15 + intensity * 0.75) + ")";
        html +=
          '<div class="analytics-heatmap-cell" style="background:' +
          bg +
          '" title="' +
          dayNames[d] +
          " " +
          padZero(h) +
          ":00 — условн. активность " +
          v +
          '"></div>';
      }
    }
    el.innerHTML = html;
  }

  function initCharts() {
    const kpi = document.getElementById("analyticsKpi");
    if (!kpi || typeof Chart === "undefined") return;

    kpi.innerHTML = [
      {
        cls: "accent",
        label: "Запросов к API за 24ч",
        value: "128",
        sub: "к внешнему API Аксиома24",
      },
      {
        cls: "green",
        label: "Справочников",
        value: "9",
        sub: "разделов в приложении",
      },
      {
        cls: "orange",
        label: "Записей за неделю",
        value: "342",
        sub: "создано и изменено",
      },
      {
        cls: "purple",
        label: "Ночью (22–06)",
        value: "14",
        sub: "обращений",
      },
      {
        cls: "accent",
        label: "Ср. время ответа",
        value: "240",
        sub: "мс (оценка)",
      },
      {
        cls: "red",
        label: "Ошибок API",
        value: "2",
        sub: "за период",
      },
    ]
      .map(
        (x) =>
          '<div class="analytics-kpi-card ' +
          x.cls +
          '"><div class="label">' +
          x.label +
          '</div><div class="value">' +
          x.value +
          '</div><div class="sub">' +
          x.sub +
          "</div></div>"
      )
      .join("");

    const grid = "rgba(51, 65, 85, 0.35)";
    const tick = "#94a3b8";
    Chart.defaults.color = tick;
    Chart.defaults.borderColor = grid;
    Chart.defaults.font.family = "'Montserrat', system-ui, sans-serif";

    const hourlyData = [1, 0, 0, 0, 0, 0, 2, 8, 12, 9, 6, 5, 7, 8, 6, 5, 6, 9, 10, 7, 4, 3, 2, 1];
    const camData = [0, 0, 0, 0, 0, 0, 0, 1, 2, 3, 2, 1, 2, 2, 1, 1, 2, 3, 2, 1, 1, 0, 0, 0];
    const errData = [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1];

    new Chart(document.getElementById("chartHourly"), {
      type: "bar",
      data: {
        labels: Array.from({ length: 24 }, function (_, i) {
          return padZero(i) + ":00";
        }),
        datasets: [
          {
            label: "API / справочники",
            data: hourlyData,
            backgroundColor: "#14b8a6",
            borderRadius: 4,
            barPercentage: 0.7,
          },
          {
            label: "Камеры / просмотр",
            data: camData,
            backgroundColor: "#3b82f6",
            borderRadius: 4,
            barPercentage: 0.7,
          },
          {
            label: "Ошибки",
            data: errData,
            backgroundColor: "#ef4444",
            borderRadius: 4,
            barPercentage: 0.7,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: "bottom",
            labels: { usePointStyle: true, padding: 14, font: { size: 11 } },
          },
        },
        scales: {
          x: {
            stacked: true,
            grid: { display: false },
            ticks: { font: { size: 10 }, maxRotation: 0, autoSkip: true, maxTicksLimit: 12 },
          },
          y: {
            stacked: true,
            beginAtZero: true,
            grid: { color: grid },
            ticks: { font: { size: 11 }, stepSize: 1 },
          },
        },
      },
    });

    new Chart(document.getElementById("chartVisitors"), {
      type: "doughnut",
      data: {
        labels: ["Партнёры и регионы", "Клиенты и контакты", "Камеры", "Прочее"],
        datasets: [
          {
            data: [42, 28, 18, 12],
            backgroundColor: ["#14b8a6", "#3b82f6", "#f59e0b", "#64748b"],
            borderWidth: 0,
            hoverOffset: 8,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: "65%",
        plugins: {
          legend: {
            position: "bottom",
            labels: { usePointStyle: true, padding: 14, font: { size: 11 } },
          },
        },
      },
    });

    const days = [];
    const now = new Date();
    for (let i = 6; i >= 0; i--) {
      const d = new Date(now);
      d.setDate(d.getDate() - i);
      days.push(fmtShort(d));
    }

    new Chart(document.getElementById("chart7days"), {
      type: "line",
      data: {
        labels: days,
        datasets: [
          {
            label: "Обращений всего",
            data: [95, 102, 88, 110, 105, 118, 128],
            borderColor: "#14b8a6",
            backgroundColor: "rgba(20, 184, 166, 0.12)",
            fill: true,
            tension: 0.35,
            pointRadius: 4,
            pointBackgroundColor: "#14b8a6",
          },
          {
            label: "Уникальных сессий",
            data: [12, 11, 10, 13, 12, 11, 12],
            borderColor: "#22c55e",
            backgroundColor: "rgba(34, 197, 94, 0.1)",
            fill: true,
            tension: 0.35,
            pointRadius: 4,
            pointBackgroundColor: "#22c55e",
          },
          {
            label: "Просмотров камер",
            data: [8, 9, 7, 10, 9, 11, 12],
            borderColor: "#f59e0b",
            backgroundColor: "rgba(245, 158, 11, 0.1)",
            fill: true,
            tension: 0.35,
            pointRadius: 4,
            pointBackgroundColor: "#f59e0b",
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: "bottom",
            labels: { usePointStyle: true, padding: 14, font: { size: 11 } },
          },
        },
        scales: {
          x: { grid: { display: false }, ticks: { font: { size: 11 } } },
          y: { beginAtZero: true, grid: { color: grid }, ticks: { font: { size: 11 } } },
        },
      },
    });

    renderHeatmap();

    const tbody = document.getElementById("operationsLogBody");
    if (tbody) {
      tbody.innerHTML = OPERATIONS_LOG.map(function (s) {
        return (
          "<tr><td style=\"font-variant-numeric:tabular-nums\">" +
          s.time +
          '</td><td><span style="color:' +
          s.color +
          ';font-weight:600">' +
          s.action +
          "</span> · " +
          s.detail +
          '</td><td style="font-size:12px;color:var(--text-secondary)">' +
          s.source +
          '</td><td style="font-variant-numeric:tabular-nums">' +
          s.duration +
          "</td></tr>"
        );
      }).join("");
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initCharts);
  } else {
    initCharts();
  }
})();
