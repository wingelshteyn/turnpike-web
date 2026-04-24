"""Страницы аналитики и журнала событий."""

from datetime import datetime, timedelta
from fastapi import APIRouter, Request, Query
from fastapi.responses import HTMLResponse

from ..dependencies import template_ctx, templates
from ..api.event import EventAPI
from ..config import API_BASE_URL
from ..helpers import paginate

router = APIRouter(tags=["analytics"])


@router.get("/analytics", response_class=HTMLResponse)
async def analytics(request: Request):
    return templates.TemplateResponse(request, "analytics.html", template_ctx(request))


def _enrich_event_row(r: dict) -> dict:
    """Форматирует событие из API для шаблона."""
    row = dict(r)
    
    # Парсим время события
    dt_str = row.get("Event_Time", "")
    try:
        # Формат API: 2026-04-22T21:26:00.443
        dt_obj = datetime.fromisoformat(dt_str)
        row["dt"] = dt_obj.strftime("%d.%m.%Y %H:%M")
    except ValueError:
        row["dt"] = dt_str

    # Определяем важность на основе результата
    result = row.get("Event_Result", 1)
    if result == 1:
        row["sev"] = 0
        row["sev_label"] = "Норма"
    else:
        row["sev"] = 2
        row["sev_label"] = "Высокая"

    # Статус
    row["status"] = "Обработано"
    row["st_mod"] = "done"

    # Формируем заголовок и детали
    action = "Проезд разрешен" if result == 1 else "В проезде отказано"
    row["event"] = f"{action} ({row.get('Equipment_Name', 'Неизвестно')})"
    
    client_info = []
    if row.get("Client_Name"):
        client_info.append(row["Client_Name"])
    if row.get("Event_Phone"):
        client_info.append(row["Event_Phone"])
    if row.get("Client_Place"):
        client_info.append(row["Client_Place"])
        
    row["detail"] = " · ".join(client_info) if client_info else "Нет данных"
    
    # Источник
    row["device"] = f"{row.get('Region_Name', '')} ({row.get('Region_Place', '')})"

    # Фото: в API приходит путь на сервере (filesystem), пробуем привести к веб-пути.
    photo = row.get("Event_Photo")
    photo_url = None
    if isinstance(photo, str) and photo:
        # Чаще всего storage доступен как /store/..., а в поле приходит /var/ax/ax_server/store/...
        if photo.startswith("/var/ax/ax_server/store/"):
            photo = photo.replace("/var/ax/ax_server", "", 1)  # -> /store/...
        # Если всё ещё абсолютный путь, оставляем как есть — но URL строим только для /...
        if photo.startswith("/"):
            photo_url = f"{API_BASE_URL}{photo}"
    row["photo_url"] = photo_url

    # Строка для поиска
    blob = f"{row['event']} {row['detail']} {row['device']} {row['dt']}"
    row["search_blob"] = blob.lower()
    
    return row


@router.get("/events", response_class=HTMLResponse)
async def events_journal(
    request: Request,
    date1: str = Query(None, description="Начальная дата (YYYY-MM-DD)"),
    date2: str = Query(None, description="Конечная дата (YYYY-MM-DD)"),
    page: int = Query(1, ge=1, description="Страница"),
    limit: int = Query(20, ge=1, le=500, description="Лимит (параметр API, может игнорироваться)"),
    sample: str = Query(None, description="Поиск по телефону или номеру"),
):
    # По умолчанию берем последние 7 дней
    if not date2:
        date2 = datetime.now().strftime("%Y-%m-%d")
    if not date1:
        date1 = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")

    all_rows: list[dict] = []
    rows: list[dict] = []
    error_msg = None
    
    try:
        # Внешний API не поддерживает offset/page, поэтому забираем «пакетом»
        # (до 500) и делаем пагинацию на нашей стороне.
        request_limit = 500
        async with EventAPI() as api:
            raw_events = await api.list_events(
                date1=date1,
                date2=date2,
                limit=request_limit,
                sample=sample
            )
            all_rows = [_enrich_event_row(r) for r in raw_events]
    except Exception as e:
        error_msg = f"Ошибка загрузки событий: {str(e)}"
        # Можно добавить fallback на демо-данные здесь, если нужно
        all_rows = []

    rows, total, total_pages = paginate(all_rows, page, per_page=20)

    ctx = template_ctx(
        request, 
        journal_rows=rows,
        error_msg=error_msg,
        filter_date1=date1,
        filter_date2=date2,
        filter_sample=sample or "",
        page=page,
        total_pages=total_pages,
        base_url="/events",
    )
    return templates.TemplateResponse(
        request,
        "events.html",
        context=ctx,
    )
