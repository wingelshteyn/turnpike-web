"""Маршруты для типов контактов (ContactType)."""

import logging

from fastapi import APIRouter, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse

from api import ContactTypeAPI
from dependencies import templates
from helpers import fetch_split, filter_by_query, paginate

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/contact-types", tags=["contact_types"])


@router.get("", response_class=HTMLResponse)
async def contact_types_list(request: Request, q: str = "", page: int = 1):
    async with ContactTypeAPI() as api:
        raw = await api.list(include_deleted=False)
    filtered = filter_by_query(raw, q, ["id", "Code", "Name", "created"])
    items, total, total_pages = paginate(filtered, page)
    return templates.TemplateResponse(
        "contact_types/index.html",
        {"request": request, "items": items, "q": q, "page": page, "total_pages": total_pages, "base_url": "/contact-types"},
    )


@router.get("/deleted", response_class=HTMLResponse)
async def deleted_contact_types(request: Request):
    _, deleted = await fetch_split(ContactTypeAPI)
    return templates.TemplateResponse(
        "contact_types/deleted.html", {"request": request, "items": deleted},
    )


@router.get("/add", response_class=HTMLResponse)
async def add_form(request: Request):
    return templates.TemplateResponse("contact_types/add.html", {"request": request})


@router.post("/add")
async def add_contact_type(code: str = Form(""), name: str = Form("")):
    async with ContactTypeAPI() as api:
        await api.create(code=code, name=name)
    logger.info("Создан тип контакта: code=%s, name=%s", code, name)
    return RedirectResponse(url="/contact-types", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/edit/{record_id:int}", response_class=HTMLResponse)
async def edit_form(request: Request, record_id: int):
    async with ContactTypeAPI() as api:
        item = await api.read(record_id)
    return templates.TemplateResponse(
        "contact_types/edit.html", {"request": request, "item": item},
    )


@router.post("/edit/{record_id:int}")
async def update_contact_type(
    request: Request, record_id: int,
    code: str = Form(""), name: str = Form(""),
):
    async with ContactTypeAPI() as api:
        item = await api.update(record_id, code=code, name=name)
    logger.info("Тип контакта %s обновлён", record_id)
    return templates.TemplateResponse("contact_types/edit.html", {
        "request": request,
        "item": item,
        "message": "Запись успешно обновлена",
    })


@router.post("/delete/{record_id:int}")
async def delete_contact_type(record_id: int):
    async with ContactTypeAPI() as api:
        record = await api.read(record_id)
        if record.get("deleted"):
            raise HTTPException(status_code=400, detail="Запись уже удалена")
        await api.delete(record_id)
    logger.info("Удалён тип контакта %s", record_id)
    return RedirectResponse(url="/contact-types", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/restore/{record_id:int}")
async def restore_contact_type(record_id: int):
    async with ContactTypeAPI() as api:
        await api.restore(record_id)
    logger.info("Восстановлен тип контакта %s", record_id)
    return RedirectResponse(url="/contact-types", status_code=status.HTTP_303_SEE_OTHER)
