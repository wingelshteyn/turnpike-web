"""Маршруты для городов (City)."""

import logging

from fastapi import APIRouter, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse

from ..api import CityAPI
from ..dependencies import template_ctx, templates
from ..helpers import fetch_split, filter_by_query, paginate
from ..url_prefix import redirect as prefixed_redirect
from ..reference_cache import invalidate_cities_cache

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/cities", tags=["cities"])


@router.get("", response_class=HTMLResponse)
async def cities_list(request: Request, q: str = "", page: int = 1):
    async with CityAPI() as api:
        raw = await api.list(include_deleted=False)
    filtered = filter_by_query(raw, q, ["id", "Name", "created"])
    cities, total, total_pages = paginate(filtered, page)
    return templates.TemplateResponse(
        request,
        "cities/cities.html",
        template_ctx(request, cities=cities, q=q, page=page, total_pages=total_pages, base_url="/cities"),
    )


@router.get("/deleted", response_class=HTMLResponse)
async def deleted_cities(request: Request):
    _, deleted = await fetch_split(CityAPI)
    return templates.TemplateResponse(
        request,
        "cities/deleted.html", template_ctx(request, cities=deleted),
    )


@router.get("/add", response_class=HTMLResponse)
async def add_form(request: Request):
    return templates.TemplateResponse(request, "cities/add.html", template_ctx(request))


@router.post("/add")
async def add_city(request: Request, name: str = Form(...)):
    async with CityAPI() as api:
        await api.create(name=name)
    invalidate_cities_cache()
    logger.info("Создан город %s", name)
    return prefixed_redirect(request, "/cities", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/edit/{record_id:int}", response_class=HTMLResponse)
async def edit_form(request: Request, record_id: int):
    async with CityAPI() as api:
        city = await api.read(record_id)
    return templates.TemplateResponse(
        request,
        "cities/edit.html", template_ctx(request, city=city),
    )


@router.post("/edit/{record_id:int}")
async def update_city(
    request: Request, record_id: int, name: str = Form(...),
):
    async with CityAPI() as api:
        city = await api.update(record_id, name=name)
    invalidate_cities_cache()
    logger.info("Город %s обновлён", record_id)
    return templates.TemplateResponse(request, "cities/edit.html", template_ctx(
        request,
        city=city,
        message="Запись успешно обновлена",
    ))


@router.post("/delete/{record_id:int}")
async def delete_city(request: Request, record_id: int):
    async with CityAPI() as api:
        record = await api.read(record_id)
        if record.get("deleted"):
            raise HTTPException(status_code=400, detail="Запись уже удалена")
        await api.delete(record_id)
    invalidate_cities_cache()
    logger.info("Удалена запись %s", record_id)
    return prefixed_redirect(request, "/cities", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/restore/{record_id:int}")
async def restore_city(request: Request, record_id: int):
    async with CityAPI() as api:
        await api.restore(record_id)
    invalidate_cities_cache()
    logger.info("Восстановлена запись %s", record_id)
    return prefixed_redirect(request, "/cities", status_code=status.HTTP_303_SEE_OTHER)
