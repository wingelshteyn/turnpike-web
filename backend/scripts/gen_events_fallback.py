"""Генерирует partials/events_demo_fallback.html из demo_events (однократно при изменении демо-данных)."""
from __future__ import annotations

from html import escape
from pathlib import Path

from backend.demo_events import journal_rows_for_page

BACKEND = Path(__file__).resolve().parent.parent
OUT = BACKEND / "templates" / "partials" / "events_demo_fallback.html"


def main() -> None:
    rows = journal_rows_for_page()[:8]
    lines: list[str] = [
        "{# Совпадает с journal_rows_for_page(); показ, если в шаблон не передан journal_rows. #}",
    ]
    for r in rows:
        blob = escape(str(r["search_blob"]))
        lines.append("        <tr")
        lines.append(f'          data-source="{escape(str(r["device"]))}"')
        lines.append(f'          data-status="{escape(str(r["status"]))}"')
        lines.append(f'          data-search="{blob}"')
        lines.append("        >")
        lines.append(f'          <td class="events-col-time"><time datetime="">{escape(str(r["dt"]))}</time></td>')
        lines.append("          <td>")
        lines.append(f'            <div class="events-title">{escape(str(r["event"]))}</div>')
        lines.append(f'            <div class="events-detail">{escape(str(r["detail"]))}</div>')
        lines.append("          </td>")
        lines.append(f'          <td class="events-col-src">{escape(str(r["device"]))}</td>')
        lines.append('          <td class="events-col-badge">')
        lines.append(
            f'            <span class="events-badge events-badge--sev-{r["sev"]}">'
            f'{escape(str(r["sev_label"]))}</span>'
        )
        lines.append("          </td>")
        lines.append('          <td class="events-col-badge">')
        lines.append(
            f'            <span class="events-badge events-badge--st-{r["st_mod"]}">'
            f'{escape(str(r["status"]))}</span>'
        )
        lines.append("          </td>")
        lines.append("        </tr>")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {len(rows)} rows to {OUT}")


if __name__ == "__main__":
    main()
