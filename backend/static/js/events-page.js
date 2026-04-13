/**
 * События: поиск и фильтры по строкам таблицы (строки отдаются с сервера).
 * Скрытие — через класс .events-tr--filtered, не через атрибут hidden у <tr>.
 */
(function () {
  function getFilterState() {
    var src = document.getElementById("filterSource");
    var st = document.getElementById("filterStatus");
    var searchEl = document.getElementById("eventsSearch");
    return {
      q: searchEl && searchEl.value
        ? searchEl.value.trim().toLowerCase()
        : "",
      source: src && src.value ? src.value : "",
      status: st && st.value ? st.value : "",
    };
  }

  function setCountLabel(visible) {
    var countEl = document.getElementById("eventsCountLabel");
    if (!countEl) return;
    countEl.textContent =
      visible === 0
        ? "Нет записей"
        : visible + " " + plural(visible, "запись", "записи", "записей");
  }

  function resetAllRowsVisible() {
    var tbody = document.getElementById("eventsTableBody");
    if (!tbody) return;
    tbody.querySelectorAll("tr").forEach(function (tr) {
      tr.classList.remove("events-tr--filtered");
      tr.removeAttribute("hidden");
      tr.hidden = false;
    });
  }

  function refreshCountFromDom() {
    var tbody = document.getElementById("eventsTableBody");
    if (!tbody) return;
    var rows = tbody.querySelectorAll("tr");
    var visible = 0;
    rows.forEach(function (tr) {
      if (!tr.classList.contains("events-tr--filtered")) visible += 1;
    });
    setCountLabel(visible);
  }

  function applyFilters() {
    var tbody = document.getElementById("eventsTableBody");
    if (!tbody) return;

    var f = getFilterState();
    var rows = tbody.querySelectorAll("tr");
    var visible = 0;

    if (!f.q && !f.source && !f.status) {
      rows.forEach(function (tr) {
        tr.classList.remove("events-tr--filtered");
      });
      setCountLabel(rows.length);
      return;
    }

    rows.forEach(function (tr) {
      var blob = (tr.getAttribute("data-search") || "").toLowerCase();
      var ok = true;
      if (f.q && blob.indexOf(f.q) === -1) ok = false;
      if (f.source && tr.getAttribute("data-source") !== f.source) ok = false;
      if (f.status && tr.getAttribute("data-status") !== f.status) ok = false;
      tr.classList.toggle("events-tr--filtered", !ok);
      if (ok) visible += 1;
    });

    setCountLabel(visible);
  }

  function plural(n, a, b, c) {
    var m = n % 100;
    if (m >= 11 && m <= 14) return c;
    m = n % 10;
    if (m === 1) return a;
    if (m >= 2 && m <= 4) return b;
    return c;
  }

  function openModal() {
    var el = document.getElementById("eventsFiltersOverlay");
    if (!el) return;
    el.classList.add("active");
    el.setAttribute("aria-hidden", "false");
  }

  function closeModal() {
    var el = document.getElementById("eventsFiltersOverlay");
    if (!el) return;
    el.classList.remove("active");
    el.setAttribute("aria-hidden", "true");
  }

  function init() {
    resetAllRowsVisible();
    refreshCountFromDom();

    var search = document.getElementById("eventsSearch");
    if (search) {
      search.addEventListener("focus", function clearReadonlyOnce() {
        search.removeAttribute("readonly");
        search.removeEventListener("focus", clearReadonlyOnce);
      });
      search.addEventListener("input", applyFilters);
    }

    var btn = document.getElementById("eventsFiltersBtn");
    if (btn) btn.addEventListener("click", openModal);

    var closeBtn = document.getElementById("eventsFiltersClose");
    if (closeBtn) closeBtn.addEventListener("click", closeModal);

    var apply = document.getElementById("eventsFiltersApply");
    if (apply) {
      apply.addEventListener("click", function () {
        applyFilters();
        closeModal();
      });
    }

    var overlay = document.getElementById("eventsFiltersOverlay");
    if (overlay) {
      overlay.addEventListener("click", function (e) {
        if (e.target === overlay) closeModal();
      });
    }

    var filterSource = document.getElementById("filterSource");
    var filterStatus = document.getElementById("filterStatus");
    if (filterSource) filterSource.addEventListener("change", applyFilters);
    if (filterStatus) filterStatus.addEventListener("change", applyFilters);

    document.addEventListener("keydown", function (e) {
      if (e.key !== "Escape") return;
      var o = document.getElementById("eventsFiltersOverlay");
      if (o && o.classList.contains("active")) closeModal();
    });

    // После всех синхронных обработчиков DOMContentLoaded (старый кэш, расширения)
    setTimeout(function () {
      resetAllRowsVisible();
      refreshCountFromDom();
    }, 0);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
