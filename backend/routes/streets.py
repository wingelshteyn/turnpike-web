"""Маршруты для улиц (Street)."""

import logging

from fastapi import APIRouter, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse

from ..api import CityAPI, StreetAPI
from ..dependencies import templates
from ..helpers import fetch_split, filter_by_query, normalize_streets_for_template, paginate

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/streets", tags=["streets"])


async def _streets_with_cities(include_deleted: bool = True):
    """Загрузить улицы и города, нормализовать для шаблона."""
    async with StreetAPI() as api:
        raw_streets = await api.list(include_deleted=include_deleted)
    async with CityAPI() as city_api:
        cities = await city_api.list(include_deleted=True)
    streets = normalize_streets_for_template(raw_streets, cities)
    return streets, cities


@router.get("", response_class=HTMLResponse)
async def streets_list(request: Request, q: str = "", page: int = 1):
    streets_raw, cities = await _streets_with_cities(include_deleted=False)
    filtered = filter_by_query(streets_raw, q, ["id", "name", "City", "created", "updated"])
    streets, total, total_pages = paginate(filtered, page)
    return templates.TemplateResponse("streets/streets.html", {
        "request": request,
        "streets": streets,
        "cities": cities,
        "q": q,
        "page": page,
        "total_pages": total_pages,
        "base_url": "/streets",
    })


@router.get("/deleted", response_class=HTMLResponse)
async def deleted_streets(request: Request):
    _, deleted = await fetch_split(StreetAPI)
    async with CityAPI() as city_api:
        cities = await city_api.list(include_deleted=True)
    return templates.TemplateResponse("streets/deleted.html", {
        "request": request,
        "streets": deleted,
        "cities": cities,
    })


@router.get("/add", response_class=HTMLResponse)
async def add_form(request: Request):
    async with CityAPI() as city_api:
        cities = await city_api.list(include_deleted=False)
    return templates.TemplateResponse(
        "streets/add.html", {"request": request, "cities": cities},
    )


@router.post("/add")
async def add_street(city: int = Form(...), name: str = Form(...)):
    async with StreetAPI() as api:
        await api.create(city=city, name=name)
    logger.info("Создана улица %s", name)
    return RedirectResponse(url="/streets", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/edit/{record_id:int}", response_class=HTMLResponse)
async def edit_form(request: Request, record_id: int):
    async with StreetAPI() as api:
        street = await api.read(record_id)
    async with CityAPI() as city_api:
        cities = await city_api.list(include_deleted=False)
    return templates.TemplateResponse("streets/edit.html", {
        "request": request,
        "street": street,
        "cities": cities,
    })


@router.post("/edit/{record_id:int}")
async def update_street(
    request: Request,
    record_id: int,
    city: int = Form(...),
    name: str = Form(...),
):
    async with StreetAPI() as api:
        street = await api.update(record_id, city=city, name=name)
    async with CityAPI() as city_api:
        cities = await city_api.list(include_deleted=False)
    logger.info("Улица %s обновлена", record_id)
    return templates.TemplateResponse("streets/edit.html", {
        "request": request,
        "street": street,
        "cities": cities,
        "message": "Запись успешно обновлена",
    })


@router.post("/delete/{record_id:int}")
async def delete_street(record_id: int):
    async with StreetAPI() as api:
        record = await api.read(record_id)
        if record.get("deleted"):
            raise HTTPException(status_code=400, detail="Запись уже удалена")
        await api.delete(record_id)
    logger.info("Удалена запись %s", record_id)
    return RedirectResponse(url="/streets", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/restore/{record_id:int}")
async def restore_street(record_id: int):
    async with StreetAPI() as api:
        await api.restore(record_id)
    logger.info("Восстановлена запись %s", record_id)
    return RedirectResponse(url="/streets", status_code=status.HTTP_303_SEE_OTHER)
