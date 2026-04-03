"""Маршруты для домов (House)."""

import asyncio
import logging

from fastapi import APIRouter, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse

from ..api import HouseAPI, StreetAPI
from ..dependencies import template_ctx, templates
from ..helpers import fetch_split, filter_by_query, normalize_streets_for_template, paginate
from ..reference_cache import cities_list as cities_list_cached

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/houses", tags=["houses"])


async def _streets_for_template(include_deleted: bool = True):
    """Загрузить и нормализовать улицы для шаблонов домов."""

    async def _streets():
        async with StreetAPI() as street_api:
            return await street_api.list(include_deleted=include_deleted)

    raw_streets, cities = await asyncio.gather(
        _streets(),
        cities_list_cached(include_deleted=True),
    )
    return normalize_streets_for_template(raw_streets, cities)


def _street_names(streets):
    """Сопоставление id улицы -> название для отображения."""
    result = {}
    for s in streets:
        sid = s.get("id")
        if sid is not None:
            name = s.get("name") or s.get("Name") or "—"
            result[str(sid)] = name
    return result


@router.get("", response_class=HTMLResponse)
async def houses_list(request: Request, q: str = "", page: int = 1):
    async def _fetch_houses():
        async with HouseAPI() as api:
            return await api.list(include_deleted=False)

    raw, streets = await asyncio.gather(
        _fetch_houses(),
        _streets_for_template(include_deleted=True),
    )
    street_names = _street_names(streets)
    filtered = filter_by_query(raw, q, ["id", "Number", "Street", "street", "f_Street", "created", "updated"])
    houses, total, total_pages = paginate(filtered, page)
    return templates.TemplateResponse("houses/houses.html", template_ctx(
        request,
        houses=houses,
        streets=streets,
        street_names=street_names,
        q=q,
        page=page,
        total_pages=total_pages,
        base_url="/houses",
    ))


@router.get("/deleted", response_class=HTMLResponse)
async def deleted_houses(request: Request):
    _, deleted = await fetch_split(HouseAPI)
    streets = await _streets_for_template(include_deleted=True)
    street_names = _street_names(streets)
    return templates.TemplateResponse("houses/deleted.html", template_ctx(
        request,
        houses=deleted,
        streets=streets,
        street_names=street_names,
    ))


@router.get("/add", response_class=HTMLResponse)
async def add_form(request: Request):
    streets = await _streets_for_template(include_deleted=False)
    return templates.TemplateResponse(
        "houses/add.html", template_ctx(request, streets=streets),
    )


@router.post("/add")
async def add_house(street: int = Form(...), number: str = Form(...)):
    async with HouseAPI() as api:
        await api.create(street=street, number=number)
    logger.info("Создан дом %s", number)
    return RedirectResponse(url="/houses", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/edit/{record_id:int}", response_class=HTMLResponse)
async def edit_form(request: Request, record_id: int):
    async def _read_house():
        async with HouseAPI() as api:
            return await api.read(record_id)

    house, streets = await asyncio.gather(
        _read_house(),
        _streets_for_template(include_deleted=False),
    )
    return templates.TemplateResponse("houses/edit.html", template_ctx(
        request,
        house=house,
        streets=streets,
    ))


@router.post("/edit/{record_id:int}")
async def update_house(
    request: Request,
    record_id: int,
    street: int = Form(...),
    number: str = Form(...),
):
    async with HouseAPI() as api:
        house = await api.update(record_id, street=street, number=number)
    streets = await _streets_for_template(include_deleted=False)
    logger.info("Дом %s обновлён", record_id)
    return templates.TemplateResponse("houses/edit.html", template_ctx(
        request,
        house=house,
        streets=streets,
        message="Запись успешно обновлена",
    ))


@router.post("/delete/{record_id:int}")
async def delete_house(record_id: int):
    async with HouseAPI() as api:
        record = await api.read(record_id)
        if record.get("deleted"):
            raise HTTPException(status_code=400, detail="Запись уже удалена")
        await api.delete(record_id)
    logger.info("Удалена запись %s", record_id)
    return RedirectResponse(url="/houses", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/restore/{record_id:int}")
async def restore_house(record_id: int):
    async with HouseAPI() as api:
        await api.restore(record_id)
    logger.info("Восстановлена запись %s", record_id)
    return RedirectResponse(url="/houses", status_code=status.HTTP_303_SEE_OTHER)
