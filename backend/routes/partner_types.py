"""Маршруты для типов партнёров (PartnerType)."""

import logging

from fastapi import APIRouter, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse

from ..api import PartnerTypeAPI
from ..dependencies import templates
from ..helpers import fetch_split, filter_by_query, paginate

logger = logging.getLogger(__name__)

router = APIRouter(tags=["partner_types"])


def _ctx(request: Request, **kwargs):
    """Собрать контекст шаблона с именем пользователя."""
    ctx = {"request": request, "username": getattr(request.state, "username", None)}
    ctx.update(kwargs)
    return ctx


@router.get("/", response_class=HTMLResponse, name="index")
async def partner_types_list(request: Request, q: str = "", page: int = 1):
    active, _ = await fetch_split(PartnerTypeAPI)
    active = filter_by_query(active, q, ["id", "Brief", "Name", "city", "code", "created"])
    items, total, total_pages = paginate(active, page)
    return templates.TemplateResponse(
        "index.html",
        _ctx(request, partners=items, q=q, page=page, total_pages=total_pages, base_url="/"),
    )


@router.get("/deleted", response_class=HTMLResponse)
async def deleted_partner_types(request: Request):
    _, deleted = await fetch_split(PartnerTypeAPI)
    return templates.TemplateResponse("deleted.html", _ctx(request, partners=deleted))


@router.get("/add", response_class=HTMLResponse)
async def add_form(request: Request):
    return templates.TemplateResponse("add.html", _ctx(request))


@router.post("/add")
async def add_partner_type(type: str = Form(...), name: str = Form(...)):
    async with PartnerTypeAPI() as api:
        await api.create(brief=type, name=name)
    logger.info("Создан тип партнёра %s / %s", type, name)
    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/edit/{record_id:int}", response_class=HTMLResponse)
async def edit_form(request: Request, record_id: int):
    async with PartnerTypeAPI() as api:
        partner = await api.read(record_id)
    return templates.TemplateResponse("edit.html", _ctx(request, partner=partner))


@router.post("/edit/{record_id:int}")
async def update_partner_type(
    request: Request,
    record_id: int,
    type: str = Form(...),
    name: str = Form(...),
):
    async with PartnerTypeAPI() as api:
        partner = await api.update(record_id, brief=type, name=name)
    logger.info("Запись %s обновлена", record_id)
    return templates.TemplateResponse(
        "edit.html",
        _ctx(request, partner=partner, message="Запись успешно обновлена"),
    )


@router.post("/delete/{record_id:int}")
async def delete_partner_type(record_id: int):
    async with PartnerTypeAPI() as api:
        record = await api.read(record_id)
        if record.get("deleted"):
            raise HTTPException(status_code=400, detail="Запись уже удалена")
        await api.delete(record_id)
    logger.info("Удалена запись %s", record_id)
    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/restore/{record_id:int}")
async def restore_partner_type(record_id: int):
    async with PartnerTypeAPI() as api:
        await api.restore(record_id)
    logger.info("Восстановлена запись %s", record_id)
    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
