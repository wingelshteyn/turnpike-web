"""Маршруты для типов территорий (RegionType)."""

import logging

from fastapi import APIRouter, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse

from api import RegionTypeAPI
from dependencies import templates
from helpers import fetch_split, filter_by_query, paginate

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/region-types", tags=["region_types"])


def _ctx(request: Request, **kwargs):
    ctx = {"request": request, "username": getattr(request.state, "username", None)}
    ctx.update(kwargs)
    return ctx


@router.get("", response_class=HTMLResponse)
async def region_types_list(request: Request, q: str = "", page: int = 1):
    active, _ = await fetch_split(RegionTypeAPI)
    filtered = filter_by_query(active, q, ["id", "Brief", "Name", "created"])
    territories, total, total_pages = paginate(filtered, page)
    return templates.TemplateResponse(
        "region_types/territories.html",
        _ctx(request, territories=territories, q=q, page=page, total_pages=total_pages, base_url="/region-types"),
    )


@router.get("/deleted", response_class=HTMLResponse)
async def deleted_region_types(request: Request):
    _, deleted = await fetch_split(RegionTypeAPI)
    return templates.TemplateResponse(
        "region_types/deleted.html", _ctx(request, regions=deleted),
    )


@router.get("/add", response_class=HTMLResponse)
async def add_form(request: Request):
    return templates.TemplateResponse("region_types/add.html", _ctx(request))


@router.post("/add")
async def add_region_type(type: str = Form(...), name: str = Form(...)):
    async with RegionTypeAPI() as api:
        await api.create(brief=type, name=name)
    logger.info("Создан тип территории %s / %s", type, name)
    return RedirectResponse(url="/region-types", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/edit/{record_id:int}", response_class=HTMLResponse)
async def edit_form(request: Request, record_id: int):
    async with RegionTypeAPI() as api:
        region = await api.read(record_id)
    return templates.TemplateResponse(
        "region_types/edit.html", _ctx(request, region=region),
    )


@router.post("/edit/{record_id:int}")
async def update_region_type(
    request: Request,
    record_id: int,
    type: str = Form(...),
    name: str = Form(...),
):
    async with RegionTypeAPI() as api:
        region = await api.update(record_id, brief=type, name=name)
    logger.info("Тип территории %s обновлён", record_id)
    return templates.TemplateResponse(
        "region_types/edit.html",
        _ctx(request, region=region, message="Запись обновлена"),
    )


@router.post("/delete/{record_id:int}")
async def delete_region_type(record_id: int):
    async with RegionTypeAPI() as api:
        record = await api.read(record_id)
        if record.get("deleted"):
            raise HTTPException(status_code=400, detail="Запись уже удалена")
        await api.delete(record_id)
    logger.info("Удалена запись %s", record_id)
    return RedirectResponse(url="/region-types", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/restore/{record_id:int}")
async def restore_region_type(record_id: int):
    async with RegionTypeAPI() as api:
        await api.restore(record_id)
    logger.info("Восстановлена запись %s", record_id)
    return RedirectResponse(url="/region-types", status_code=status.HTTP_303_SEE_OTHER)
