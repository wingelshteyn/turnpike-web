"""Страницы аналитики и журнала событий (демо-данные, UI в стиле приложения)."""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from ..dependencies import template_ctx, templates
from ..demo_events import journal_rows_for_page

router = APIRouter(tags=["analytics"])


@router.get("/analytics", response_class=HTMLResponse)
async def analytics(request: Request):
    return templates.TemplateResponse(request, "analytics.html", template_ctx(request))


@router.get("/events", response_class=HTMLResponse)
async def events_journal(request: Request):
    rows = journal_rows_for_page()
    ctx = template_ctx(request, journal_rows=rows)
    return templates.TemplateResponse(
        request,
        "events.html",
        context=ctx,
    )
