/**
 * События: поиск и фильтры по строкам таблицы (строки отдаются с сервера).
 * Скрытие — через класс .events-tr--filtered, не через атрибут hidden у <tr>.
 */
(function () {
  var dpState = {
    popover: null,
    activeInput: null,
    viewYear: null,
    viewMonth: null, // 0..11
  };

  function getFilterState() {
    var searchEl = document.getElementById("eventsSearch");
    return {
      q: searchEl && searchEl.value
        ? searchEl.value.trim().toLowerCase()
        : ""
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
      if (!tr.classList.contains("events-tr--filtered") && tr.children.length > 1) visible += 1;
    });
    setCountLabel(visible);
  }

  function applyFilters() {
    var tbody = document.getElementById("eventsTableBody");
    if (!tbody) return;

    var f = getFilterState();
    var rows = tbody.querySelectorAll("tr");
    var visible = 0;

    if (!f.q) {
      rows.forEach(function (tr) {
        tr.classList.remove("events-tr--filtered");
      });
      refreshCountFromDom();
      return;
    }

    rows.forEach(function (tr) {
      // Игнорируем строку с сообщением об отсутствии данных
      if (tr.children.length <= 1) return;
      
      var blob = (tr.getAttribute("data-search") || "").toLowerCase();
      var ok = true;
      if (f.q && blob.indexOf(f.q) === -1) ok = false;
      
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

  function parseYmd(value) {
    var m = /^(\d{4})-(\d{2})-(\d{2})$/.exec((value || "").trim());
    if (!m) return null;
    var y = Number(m[1]);
    var mo = Number(m[2]) - 1;
    var d = Number(m[3]);
    var dt = new Date(y, mo, d);
    // Проверяем, что дата валидна и не "перепрыгнула"
    if (dt.getFullYear() !== y || dt.getMonth() !== mo || dt.getDate() !== d) return null;
    return dt;
  }

  function fmt2(n) {
    return (n < 10 ? "0" : "") + String(n);
  }

  function formatYmd(date) {
    return date.getFullYear() + "-" + fmt2(date.getMonth() + 1) + "-" + fmt2(date.getDate());
  }

  function daysInMonth(y, m0) {
    return new Date(y, m0 + 1, 0).getDate();
  }

  function ensurePopover() {
    if (dpState.popover) return dpState.popover;
    var el = document.createElement("div");
    el.className = "tp-datepicker-popover";
    el.setAttribute("role", "dialog");
    el.setAttribute("aria-label", "Выбор даты");
    el.style.display = "none";
    document.body.appendChild(el);
    dpState.popover = el;
    return el;
  }

  function buildCalendarHtml(year, month0, selectedDate) {
    var monthNames = [
      "Январь","Февраль","Март","Апрель","Май","Июнь",
      "Июль","Август","Сентябрь","Октябрь","Ноябрь","Декабрь"
    ];
    var dows = ["Пн","Вт","Ср","Чт","Пт","Сб","Вс"];
    var first = new Date(year, month0, 1);
    // JS: 0=вс..6=сб; нам нужно пн=0..вс=6
    var jsDow = first.getDay();
    var dow = (jsDow + 6) % 7;
    var dim = daysInMonth(year, month0);

    var today = new Date();
    var todayKey = formatYmd(new Date(today.getFullYear(), today.getMonth(), today.getDate()));
    var selKey = selectedDate ? formatYmd(selectedDate) : null;

    var html = "";
    html += '<div class="tp-datepicker-header">';
    html += '  <button type="button" class="tp-datepicker-nav" data-dp-nav="-1" aria-label="Предыдущий месяц">‹</button>';
    html += '  <div class="tp-datepicker-title">' + monthNames[month0] + " " + year + "</div>";
    html += '  <button type="button" class="tp-datepicker-nav" data-dp-nav="1" aria-label="Следующий месяц">›</button>';
    html += "</div>";

    html += '<div class="tp-datepicker-grid">';
    for (var i = 0; i < dows.length; i++) {
      html += '<div class="tp-datepicker-dow">' + dows[i] + "</div>";
    }

    // Заполняем 6 недель (42 ячейки) чтобы не прыгала высота
    var totalCells = 42;
    var prevMonth0 = month0 - 1;
    var prevYear = year;
    if (prevMonth0 < 0) { prevMonth0 = 11; prevYear -= 1; }
    var prevDim = daysInMonth(prevYear, prevMonth0);

    for (var cell = 0; cell < totalCells; cell++) {
      var dayNum = cell - dow + 1;
      var out = false;
      var y = year, m = month0, d = dayNum;
      if (dayNum <= 0) {
        out = true;
        y = prevYear; m = prevMonth0; d = prevDim + dayNum;
      } else if (dayNum > dim) {
        out = true;
        var nextMonth0 = month0 + 1;
        var nextYear = year;
        if (nextMonth0 > 11) { nextMonth0 = 0; nextYear += 1; }
        y = nextYear; m = nextMonth0; d = dayNum - dim;
      }

      var key = y + "-" + fmt2(m + 1) + "-" + fmt2(d);
      var cls = "tp-datepicker-day";
      if (out) cls += " is-out";
      if (key === todayKey) cls += " is-today";
      if (selKey && key === selKey) cls += " is-selected";
      html += '<button type="button" class="' + cls + '" data-dp-date="' + key + '">' + d + "</button>";
    }
    html += "</div>";
    return html;
  }

  function openDatepickerFor(input) {
    var pop = ensurePopover();
    dpState.activeInput = input;
    var selected = parseYmd(input.value);
    var base = selected || new Date();
    dpState.viewYear = base.getFullYear();
    dpState.viewMonth = base.getMonth();
    pop.innerHTML = buildCalendarHtml(dpState.viewYear, dpState.viewMonth, selected);
    pop.style.display = "block";
    positionPopover(pop, input);
  }

  function closeDatepicker() {
    var pop = ensurePopover();
    pop.style.display = "none";
    dpState.activeInput = null;
  }

  function positionPopover(pop, input) {
    var r = input.getBoundingClientRect();
    var margin = 8;
    var top = r.bottom + margin;
    var left = r.left;

    // Не вылезаем за экран
    var vw = Math.max(document.documentElement.clientWidth || 0, window.innerWidth || 0);
    var vh = Math.max(document.documentElement.clientHeight || 0, window.innerHeight || 0);
    var width = 292;
    var height = 360;
    if (left + width > vw - 10) left = Math.max(10, vw - width - 10);
    if (top + height > vh - 10) top = Math.max(10, r.top - height - margin);

    pop.style.left = Math.round(left) + "px";
    pop.style.top = Math.round(top) + "px";
  }

  function onDatepickerClick(e) {
    var pop = dpState.popover;
    if (!pop || pop.style.display === "none") return;

    var nav = e.target && e.target.getAttribute ? e.target.getAttribute("data-dp-nav") : null;
    if (nav) {
      var dir = Number(nav);
      var y = dpState.viewYear;
      var m = dpState.viewMonth + dir;
      if (m < 0) { m = 11; y -= 1; }
      if (m > 11) { m = 0; y += 1; }
      dpState.viewYear = y;
      dpState.viewMonth = m;
      var selected = dpState.activeInput ? parseYmd(dpState.activeInput.value) : null;
      pop.innerHTML = buildCalendarHtml(y, m, selected);
      if (dpState.activeInput) positionPopover(pop, dpState.activeInput);
      return;
    }

    var date = e.target && e.target.getAttribute ? e.target.getAttribute("data-dp-date") : null;
    if (date && dpState.activeInput) {
      dpState.activeInput.value = date;
      closeDatepicker();
      dpState.activeInput.dispatchEvent(new Event("change", { bubbles: true }));
    }
  }

  function initDatepickers() {
    var from = document.getElementById("filterFrom");
    var to = document.getElementById("filterTo");
    var inputs = [from, to].filter(Boolean);
    if (!inputs.length) return;

    ensurePopover();
    dpState.popover.addEventListener("click", onDatepickerClick);

    inputs.forEach(function (inp) {
      inp.addEventListener("focus", function () { openDatepickerFor(inp); });
      inp.addEventListener("click", function () { openDatepickerFor(inp); });
      inp.addEventListener("keydown", function (e) {
        if (e.key === "Escape") closeDatepicker();
      });
      inp.addEventListener("blur", function () {
        // легкая валидация: если пользователь ввёл руками криво — оставляем как есть
        // (сервер в любом случае подставит дефолт, но значение сохраняем, чтобы человек увидел)
      });
    });

    window.addEventListener("resize", function () {
      if (dpState.activeInput && dpState.popover && dpState.popover.style.display !== "none") {
        positionPopover(dpState.popover, dpState.activeInput);
      }
    });

    document.addEventListener("mousedown", function (e) {
      var pop = dpState.popover;
      if (!pop || pop.style.display === "none") return;
      if (e.target === pop || pop.contains(e.target)) return;
      if (dpState.activeInput && (e.target === dpState.activeInput || dpState.activeInput.contains(e.target))) return;
      closeDatepicker();
    });
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

    var overlay = document.getElementById("eventsFiltersOverlay");
    if (overlay) {
      overlay.addEventListener("click", function (e) {
        if (e.target === overlay) closeModal();
      });
    }

    document.addEventListener("keydown", function (e) {
      if (e.key !== "Escape") return;
      var o = document.getElementById("eventsFiltersOverlay");
      if (o && o.classList.contains("active")) closeModal();
    });

    initDatepickers();

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
