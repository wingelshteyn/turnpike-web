"""Маршруты для партнёров (Partner)."""

import asyncio
import logging

from fastapi import APIRouter, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse

from ..api import PartnerAPI
from ..dependencies import template_ctx, templates
from ..helpers import fetch_split, filter_by_query, paginate
from ..url_prefix import redirect as prefixed_redirect
from ..reference_cache import partner_types_list as partner_types_list_cached

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/partners", tags=["partners"])


def _partner_type_names(partner_types):
    """Сопоставление id типа -> название для отображения."""
    return {str(pt.get("id")): (pt.get("Name") or "—") for pt in partner_types}


@router.get("", response_class=HTMLResponse)
async def partners_list(request: Request, q: str = "", page: int = 1):
    async def _fetch_partners():
        async with PartnerAPI() as api:
            return await api.list(include_deleted=False)

    raw, partner_types = await asyncio.gather(
        _fetch_partners(),
        partner_types_list_cached(),
    )
    partner_type_names = _partner_type_names(partner_types)
    filtered = filter_by_query(raw, q, ["id", "Name", "PartnerType", "f_PartnerType", "created", "updated"])
    partners, total, total_pages = paginate(filtered, page)
    return templates.TemplateResponse(request, "partners/partners.html", template_ctx(
        request, partners=partners, partner_types=partner_types,
        partner_type_names=partner_type_names, q=q,
        page=page, total_pages=total_pages, base_url="/partners",
    ))


@router.get("/deleted", response_class=HTMLResponse)
async def deleted_partners(request: Request):
    _, deleted = await fetch_split(PartnerAPI)
    partner_types = await partner_types_list_cached()
    partner_type_names = _partner_type_names(partner_types)
    return templates.TemplateResponse(request, "partners/deleted.html", template_ctx(
        request, partners=deleted, partner_types=partner_types,
        partner_type_names=partner_type_names,
    ))


@router.get("/add", response_class=HTMLResponse)
async def add_form(request: Request):
    partner_types = await partner_types_list_cached()
    return templates.TemplateResponse(
        request,
        "partners/add.html", template_ctx(request, partner_types=partner_types),
    )


@router.post("/add")
async def add_partner(request: Request, partner_type: int = Form(...), name: str = Form(...)):
    async with PartnerAPI() as api:
        await api.create(partner_type=partner_type, name=name)
    logger.info("Создан партнёр %s с типом %s", name, partner_type)
    return prefixed_redirect(request, "/partners", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/edit/{record_id:int}", response_class=HTMLResponse)
async def edit_form(request: Request, record_id: int):
    async def _read_partner():
        async with PartnerAPI() as api:
            return await api.read(record_id)

    partner, partner_types = await asyncio.gather(
        _read_partner(),
        partner_types_list_cached(),
    )
    return templates.TemplateResponse(request, "partners/edit.html", template_ctx(
        request, partner=partner, partner_types=partner_types,
    ))


@router.post("/edit/{record_id:int}")
async def update_partner(
    request: Request,
    record_id: int,
    partner_type: int = Form(...),
    name: str = Form(...),
):
    async with PartnerAPI() as api:
        partner = await api.update(record_id, partner_type=partner_type, name=name)
    partner_types = await partner_types_list_cached()
    logger.info("Партнёр %s обновлён", record_id)
    return templates.TemplateResponse(request, "partners/edit.html", template_ctx(
        request, partner=partner, partner_types=partner_types,
        message="Запись успешно обновлена",
    ))


@router.post("/delete/{record_id:int}")
async def delete_partner(request: Request, record_id: int):
    async with PartnerAPI() as api:
        record = await api.read(record_id)
        if record.get("deleted"):
            raise HTTPException(status_code=400, detail="Запись уже удалена")
        await api.delete(record_id)
    logger.info("Удалена запись %s", record_id)
    return prefixed_redirect(request, "/partners", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/restore/{record_id:int}")
async def restore_partner(request: Request, record_id: int):
    async with PartnerAPI() as api:
        await api.restore(record_id)
    logger.info("Восстановлена запись %s", record_id)
    return prefixed_redirect(request, "/partners", status_code=status.HTTP_303_SEE_OTHER)
