"""Маршруты для партнёров (Partner)."""

import logging

from fastapi import APIRouter, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse

from ..api import PartnerAPI, PartnerTypeAPI
from ..dependencies import templates
from ..helpers import fetch_split, filter_by_query, paginate

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/partners", tags=["partners"])


def _ctx(request: Request, **kwargs):
    ctx = {"request": request, "username": getattr(request.state, "username", None)}
    ctx.update(kwargs)
    return ctx


def _partner_type_names(partner_types):
    """Сопоставление id типа -> название для отображения."""
    return {str(pt.get("id")): (pt.get("Name") or "—") for pt in partner_types}


@router.get("", response_class=HTMLResponse)
async def partners_list(request: Request, q: str = "", page: int = 1):
    async with PartnerAPI() as api:
        raw = await api.list(include_deleted=False)
    async with PartnerTypeAPI() as pt_api:
        partner_types = await pt_api.list()
    partner_type_names = _partner_type_names(partner_types)
    filtered = filter_by_query(raw, q, ["id", "Name", "PartnerType", "f_PartnerType", "created", "updated"])
    partners, total, total_pages = paginate(filtered, page)
    return templates.TemplateResponse("partners/partners.html", _ctx(
        request, partners=partners, partner_types=partner_types,
        partner_type_names=partner_type_names, q=q,
        page=page, total_pages=total_pages, base_url="/partners",
    ))


@router.get("/deleted", response_class=HTMLResponse)
async def deleted_partners(request: Request):
    _, deleted = await fetch_split(PartnerAPI)
    async with PartnerTypeAPI() as pt_api:
        partner_types = await pt_api.list()
    partner_type_names = _partner_type_names(partner_types)
    return templates.TemplateResponse("partners/deleted.html", _ctx(
        request, partners=deleted, partner_types=partner_types,
        partner_type_names=partner_type_names,
    ))


@router.get("/add", response_class=HTMLResponse)
async def add_form(request: Request):
    async with PartnerTypeAPI() as api:
        partner_types = await api.list()
    return templates.TemplateResponse(
        "partners/add.html", _ctx(request, partner_types=partner_types),
    )


@router.post("/add")
async def add_partner(partner_type: int = Form(...), name: str = Form(...)):
    async with PartnerAPI() as api:
        await api.create(partner_type=partner_type, name=name)
    logger.info("Создан партнёр %s с типом %s", name, partner_type)
    return RedirectResponse(url="/partners", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/edit/{record_id:int}", response_class=HTMLResponse)
async def edit_form(request: Request, record_id: int):
    async with PartnerAPI() as api:
        partner = await api.read(record_id)
    async with PartnerTypeAPI() as pt_api:
        partner_types = await pt_api.list()
    return templates.TemplateResponse("partners/edit.html", _ctx(
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
    async with PartnerTypeAPI() as pt_api:
        partner_types = await pt_api.list()
    logger.info("Партнёр %s обновлён", record_id)
    return templates.TemplateResponse("partners/edit.html", _ctx(
        request, partner=partner, partner_types=partner_types,
        message="Запись успешно обновлена",
    ))


@router.post("/delete/{record_id:int}")
async def delete_partner(record_id: int):
    async with PartnerAPI() as api:
        record = await api.read(record_id)
        if record.get("deleted"):
            raise HTTPException(status_code=400, detail="Запись уже удалена")
        await api.delete(record_id)
    logger.info("Удалена запись %s", record_id)
    return RedirectResponse(url="/partners", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/restore/{record_id:int}")
async def restore_partner(record_id: int):
    async with PartnerAPI() as api:
        await api.restore(record_id)
    logger.info("Восстановлена запись %s", record_id)
    return RedirectResponse(url="/partners", status_code=status.HTTP_303_SEE_OTHER)
