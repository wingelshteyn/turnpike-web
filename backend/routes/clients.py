"""Маршруты для клиентов (Client)."""

import logging
from typing import Optional

from fastapi import APIRouter, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse

from ..api import ClientAPI
from ..dependencies import template_ctx, templates
from ..helpers import fetch_split, filter_by_query, paginate
from ..url_prefix import redirect as prefixed_redirect

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/clients", tags=["clients"])


@router.get("", response_class=HTMLResponse)
async def clients_list(request: Request, q: str = "", page: int = 1):
    async with ClientAPI() as api:
        raw = await api.list(include_deleted=False)
    filtered = filter_by_query(raw, q, ["id", "Name", "Place", "House", "Apart", "created"])
    items, total, total_pages = paginate(filtered, page)
    return templates.TemplateResponse(
        "clients/index.html",
        template_ctx(request, items=items, q=q, page=page, total_pages=total_pages, base_url="/clients"),
    )


@router.get("/deleted", response_class=HTMLResponse)
async def deleted_clients(request: Request):
    _, deleted = await fetch_split(ClientAPI)
    return templates.TemplateResponse(
        "clients/deleted.html", template_ctx(request, items=deleted),
    )


@router.get("/add", response_class=HTMLResponse)
async def add_form(request: Request):
    return templates.TemplateResponse("clients/add.html", template_ctx(request))


@router.post("/add")
async def add_client(
    request: Request,
    name: str = Form(""),
    place: str = Form(""),
    house: Optional[str] = Form(None),
    apart: str = Form(""),
):
    house_int = int(house) if house and house.strip() else None
    async with ClientAPI() as api:
        await api.create(name=name, place=place, house=house_int, apart=apart or None)
    logger.info("Создан клиент: %s", name)
    return prefixed_redirect(request, "/clients", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/edit/{record_id:int}", response_class=HTMLResponse)
async def edit_form(request: Request, record_id: int):
    async with ClientAPI() as api:
        item = await api.read(record_id)
    return templates.TemplateResponse(
        "clients/edit.html", template_ctx(request, item=item),
    )


@router.post("/edit/{record_id:int}")
async def update_client(
    request: Request, record_id: int,
    name: str = Form(""),
    place: str = Form(""),
    house: Optional[str] = Form(None),
    apart: str = Form(""),
):
    house_int = int(house) if house and house.strip() else None
    async with ClientAPI() as api:
        item = await api.update(record_id, name=name, place=place, house=house_int, apart=apart or None)
    logger.info("Клиент %s обновлён", record_id)
    return templates.TemplateResponse("clients/edit.html", template_ctx(
        request,
        item=item,
        message="Запись успешно обновлена",
    ))


@router.post("/delete/{record_id:int}")
async def delete_client(request: Request, record_id: int):
    async with ClientAPI() as api:
        record = await api.read(record_id)
        if record.get("deleted"):
            raise HTTPException(status_code=400, detail="Запись уже удалена")
        await api.delete(record_id)
    logger.info("Удалён клиент %s", record_id)
    return prefixed_redirect(request, "/clients", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/restore/{record_id:int}")
async def restore_client(request: Request, record_id: int):
    async with ClientAPI() as api:
        await api.restore(record_id)
    logger.info("Восстановлен клиент %s", record_id)
    return prefixed_redirect(request, "/clients", status_code=status.HTTP_303_SEE_OTHER)
