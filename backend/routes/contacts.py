"""Маршруты для контактов (Contact)."""

import asyncio
import logging
from typing import Optional

from fastapi import APIRouter, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse

from ..api import ClientAPI, ContactAPI, ContactTypeAPI
from ..dependencies import template_ctx, templates
from ..helpers import fetch_split, filter_by_query, paginate
from ..url_prefix import redirect as prefixed_redirect

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/contacts", tags=["contacts"])


@router.get("", response_class=HTMLResponse)
async def contacts_list(request: Request, q: str = "", page: int = 1):
    async with ContactAPI() as api:
        raw = await api.list(include_deleted=False)
    filtered = filter_by_query(raw, q, ["id", "Client", "ContactType", "Contact", "created"])
    items, total, total_pages = paginate(filtered, page)
    return templates.TemplateResponse(
        "contacts/index.html",
        template_ctx(request, items=items, q=q, page=page, total_pages=total_pages, base_url="/contacts"),
    )


@router.get("/deleted", response_class=HTMLResponse)
async def deleted_contacts(request: Request):
    _, deleted = await fetch_split(ContactAPI)
    return templates.TemplateResponse(
        "contacts/deleted.html", template_ctx(request, items=deleted),
    )


@router.get("/add", response_class=HTMLResponse)
async def add_form(request: Request):
    async def _clients():
        async with ClientAPI() as api:
            return await api.case()

    async def _types():
        async with ContactTypeAPI() as api:
            return await api.case()

    clients, contact_types = await asyncio.gather(_clients(), _types())
    return templates.TemplateResponse("contacts/add.html", template_ctx(
        request,
        clients=clients,
        contact_types=contact_types,
    ))


@router.post("/add")
async def add_contact(
    request: Request,
    client_id: int = Form(...),
    contact_type_id: int = Form(...),
    contact: str = Form(""),
):
    async with ContactAPI() as api:
        await api.create(client_id=client_id, contact_type_id=contact_type_id, contact=contact)
    logger.info("Создан контакт для клиента %s", client_id)
    return prefixed_redirect(request, "/contacts", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/edit/{record_id:int}", response_class=HTMLResponse)
async def edit_form(request: Request, record_id: int):
    async def _read_item():
        async with ContactAPI() as api:
            return await api.read(record_id)

    async def _clients():
        async with ClientAPI() as api:
            return await api.case()

    async def _types():
        async with ContactTypeAPI() as api:
            return await api.case()

    item, clients, contact_types = await asyncio.gather(_read_item(), _clients(), _types())
    return templates.TemplateResponse("contacts/edit.html", template_ctx(
        request,
        item=item,
        clients=clients,
        contact_types=contact_types,
    ))


@router.post("/edit/{record_id:int}")
async def update_contact(
    request: Request, record_id: int,
    client_id: int = Form(...),
    contact_type_id: int = Form(...),
    contact: str = Form(""),
):
    async def _clients():
        async with ClientAPI() as api:
            return await api.case()

    async def _types():
        async with ContactTypeAPI() as api:
            return await api.case()

    async with ContactAPI() as api:
        item = await api.update(record_id, client_id=client_id, contact_type_id=contact_type_id, contact=contact)
    clients, contact_types = await asyncio.gather(_clients(), _types())
    logger.info("Контакт %s обновлён", record_id)
    return templates.TemplateResponse("contacts/edit.html", template_ctx(
        request,
        item=item,
        clients=clients,
        contact_types=contact_types,
        message="Запись успешно обновлена",
    ))


@router.post("/delete/{record_id:int}")
async def delete_contact(request: Request, record_id: int):
    async with ContactAPI() as api:
        record = await api.read(record_id)
        if record.get("deleted"):
            raise HTTPException(status_code=400, detail="Запись уже удалена")
        await api.delete(record_id)
    logger.info("Удалён контакт %s", record_id)
    return prefixed_redirect(request, "/contacts", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/restore/{record_id:int}")
async def restore_contact(request: Request, record_id: int):
    async with ContactAPI() as api:
        await api.restore(record_id)
    logger.info("Восстановлен контакт %s", record_id)
    return prefixed_redirect(request, "/contacts", status_code=status.HTTP_303_SEE_OTHER)
