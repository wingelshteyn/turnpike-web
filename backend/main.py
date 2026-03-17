"""Точка входа приложения: создание FastAPI-приложения и подключение маршрутов."""

import logging
import sys
from pathlib import Path

# Гарантируем, что директория backend/ находится в sys.path,
# чтобы импорты работали независимо от того, откуда запущен скрипт.
BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import uvicorn
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from starlette.responses import RedirectResponse, Response

from config import STATIC_DIR
from routes import (
    auth_router,
    cameras_router,
    cities_router,
    houses_router,
    partner_types_router,
    partners_router,
    region_types_router,
    regions_router,
    streets_router,
    contact_types_router,
    clients_router,
    contacts_router,
)

from user_store import init_users

logging.basicConfig(level=logging.INFO)

app = FastAPI()

# --- Инициализация пользователей (admin / admin) ---
init_users()

# --- Статические файлы ---
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


# --- Middleware: проверка аутентификации ---
@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    """Проверяет наличие сессии. Без авторизации доступна только /auth и статика."""
    path = request.url.path

    # Разрешаем доступ без авторизации
    if (
        path in ("/auth", "/favicon.ico")
        or path.startswith("/static/")
    ):
        return await call_next(request)

    # Проверяем наличие сессионной куки
    session = request.cookies.get("session")
    if not session:
        return RedirectResponse(url="/auth", status_code=302)

    # Сохраняем имя пользователя в state для использования в шаблонах
    request.state.username = request.cookies.get("username", "user")
    return await call_next(request)


# --- Маршруты ---
app.include_router(auth_router)
app.include_router(partner_types_router)
app.include_router(region_types_router)
app.include_router(partners_router)
app.include_router(regions_router)
app.include_router(cities_router)
app.include_router(streets_router)
app.include_router(houses_router)
app.include_router(contact_types_router)
app.include_router(clients_router)
app.include_router(contacts_router)
app.include_router(cameras_router)


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return Response(status_code=204)


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        reload_dirs=[str(BACKEND_DIR)],
    )
