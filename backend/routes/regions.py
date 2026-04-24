"""Маршруты для территорий (Region)."""

import asyncio
import logging

from fastapi import APIRouter, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse

from ..api import PartnerAPI, RegionAPI
from ..dependencies import template_ctx, templates
from ..helpers import fetch_split, filter_by_query, paginate
from ..url_prefix import redirect as prefixed_redirect
from ..reference_cache import region_types_list as region_types_list_cached

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/regions", tags=["regions"])


async def _region_context():
    """Загрузить справочники (партнёры + типы территорий) для шаблона."""

    async def _partners():
        async with PartnerAPI() as api:
            return await api.list()

    partners, region_types = await asyncio.gather(
        _partners(),
        region_types_list_cached(),
    )
    return partners, region_types


@router.get("", response_class=HTMLResponse)
async def regions_list(request: Request, q: str = "", page: int = 1):
    async def _fetch_regions():
        async with RegionAPI() as api:
            return await api.list(include_deleted=False)

    async def _fetch_partners():
        async with PartnerAPI() as api:
            return await api.list()

    raw, partners, region_types = await asyncio.gather(
        _fetch_regions(),
        _fetch_partners(),
        region_types_list_cached(),
    )
    filtered = filter_by_query(raw, q, ["id", "Name", "Place", "Partner", "RegionType", "created"])
    regions, total, total_pages = paginate(filtered, page)
    return templates.TemplateResponse(request, "regions/regions.html", template_ctx(
        request, regions=regions, partners=partners, region_types=region_types, q=q,
        page=page, total_pages=total_pages, base_url="/regions",
    ))


@router.get("/deleted", response_class=HTMLResponse)
async def deleted_regions(request: Request):
    _, deleted = await fetch_split(RegionAPI)
    partners, region_types = await _region_context()
    return templates.TemplateResponse(request, "regions/deleted.html", template_ctx(
        request, regions=deleted, partners=partners, region_types=region_types,
    ))


@router.get("/add", response_class=HTMLResponse)
async def add_form(request: Request):
    partners, region_types = await _region_context()
    return templates.TemplateResponse(request, "regions/add.html", template_ctx(
        request, partners=partners, region_types=region_types,
    ))


@router.post("/add")
async def add_region(
    request: Request,
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
    return prefixed_redirect(request, "/regions", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/edit/{record_id:int}", response_class=HTMLResponse)
async def edit_form(request: Request, record_id: int):
    async def _read_region():
        async with RegionAPI() as api:
            return await api.read(record_id)

    async def _partners_only():
        async with PartnerAPI() as api:
            return await api.list()

    region, partners, region_types = await asyncio.gather(
        _read_region(),
        _partners_only(),
        region_types_list_cached(),
    )
    return templates.TemplateResponse(request, "regions/edit.html", template_ctx(
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
    return templates.TemplateResponse(request, "regions/edit.html", template_ctx(
        request, region=region, partners=partners, region_types=region_types,
        message="Запись успешно обновлена",
    ))


@router.post("/delete/{record_id:int}")
async def delete_region(request: Request, record_id: int):
    async with RegionAPI() as api:
        record = await api.read(record_id)
        if record.get("deleted"):
            raise HTTPException(status_code=400, detail="Запись уже удалена")
        await api.delete(record_id)
    logger.info("Удалена запись %s", record_id)
    return prefixed_redirect(request, "/regions", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/restore/{record_id:int}")
async def restore_region(request: Request, record_id: int):
    async with RegionAPI() as api:
        await api.restore(record_id)
    logger.info("Восстановлена запись %s", record_id)
    return prefixed_redirect(request, "/regions", status_code=status.HTTP_303_SEE_OTHER)
