"""Маршруты для территорий (Region)."""

import logging

from fastapi import APIRouter, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse

from ..api import PartnerAPI, RegionAPI, RegionTypeAPI
from ..dependencies import templates
from ..helpers import fetch_split, filter_by_query, paginate

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/regions", tags=["regions"])


def _ctx(request: Request, **kwargs):
    ctx = {"request": request, "username": getattr(request.state, "username", None)}
    ctx.update(kwargs)
    return ctx


async def _region_context():
    """Загрузить справочники (партнёры + типы территорий) для шаблона."""
    async with PartnerAPI() as p_api:
        partners = await p_api.list()
    async with RegionTypeAPI() as rt_api:
        region_types = await rt_api.list()
    return partners, region_types


@router.get("", response_class=HTMLResponse)
async def regions_list(request: Request, q: str = "", page: int = 1):
    async with RegionAPI() as api:
        raw = await api.list(include_deleted=False)
    partners, region_types = await _region_context()
    filtered = filter_by_query(raw, q, ["id", "Name", "Place", "Partner", "RegionType", "created"])
    regions, total, total_pages = paginate(filtered, page)
    return templates.TemplateResponse("regions/regions.html", _ctx(
        request, regions=regions, partners=partners, region_types=region_types, q=q,
        page=page, total_pages=total_pages, base_url="/regions",
    ))


@router.get("/deleted", response_class=HTMLResponse)
async def deleted_regions(request: Request):
    _, deleted = await fetch_split(RegionAPI)
    partners, region_types = await _region_context()
    return templates.TemplateResponse("regions/deleted.html", _ctx(
        request, regions=deleted, partners=partners, region_types=region_types,
    ))


@router.get("/add", response_class=HTMLResponse)
async def add_form(request: Request):
    partners, region_types = await _region_context()
    return templates.TemplateResponse("regions/add.html", _ctx(
        request, partners=partners, region_types=region_types,
    ))


@router.post("/add")
async def add_region(
    partner: int = Form(...),
    region_type: int = Form(...),
    name: str = Form(...),
    place: str = Form(...),
):
    async with RegionAPI() as api:
        await api.create(
            partner=partner, region_type=region_type, name=name, place=place,
        )
    logger.info("Создана территория %s с местом %s", name, place)
    return RedirectResponse(url="/regions", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/edit/{record_id:int}", response_class=HTMLResponse)
async def edit_form(request: Request, record_id: int):
    async with RegionAPI() as api:
        region = await api.read(record_id)
    partners, region_types = await _region_context()
    return templates.TemplateResponse("regions/edit.html", _ctx(
        request, region=region, partners=partners, region_types=region_types,
    ))


@router.post("/edit/{record_id:int}")
async def update_region(
    request: Request,
    record_id: int,
    partner: int = Form(...),
    region_type: int = Form(...),
    name: str = Form(...),
    place: str = Form(...),
):
    async with RegionAPI() as api:
        region = await api.update(
            record_id, partner=partner, region_type=region_type,
            name=name, place=place,
        )
    partners, region_types = await _region_context()
    logger.info("Территория %s обновлена", record_id)
    return templates.TemplateResponse("regions/edit.html", _ctx(
        request, region=region, partners=partners, region_types=region_types,
        message="Запись успешно обновлена",
    ))


@router.post("/delete/{record_id:int}")
async def delete_region(record_id: int):
    async with RegionAPI() as api:
        record = await api.read(record_id)
        if record.get("deleted"):
            raise HTTPException(status_code=400, detail="Запись уже удалена")
        await api.delete(record_id)
    logger.info("Удалена запись %s", record_id)
    return RedirectResponse(url="/regions", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/restore/{record_id:int}")
async def restore_region(record_id: int):
    async with RegionAPI() as api:
        await api.restore(record_id)
    logger.info("Восстановлена запись %s", record_id)
    return RedirectResponse(url="/regions", status_code=status.HTTP_303_SEE_OTHER)
