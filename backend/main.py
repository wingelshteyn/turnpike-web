"""Точка входа приложения: создание FastAPI-приложения и подключение маршрутов."""

import logging
from pathlib import Path

import uvicorn
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from starlette.responses import RedirectResponse, Response
from starlette.status import HTTP_403_FORBIDDEN

from .config import STATIC_DIR
from .session_store import get_session, init_session_store
from .routes import (
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

from .user_store import init_users

logging.basicConfig(level=logging.INFO)

app = FastAPI()

# --- Инициализация пользователей (admin / admin) ---
init_users()
init_session_store()

# --- Статические файлы ---
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


# --- Middleware: проверка аутентификации ---
@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    """Проверяет валидность сессии. Без авторизации доступна только /auth и статика."""
    path = request.url.path

    # Разрешаем доступ без авторизации
    if (
        path in ("/auth", "/favicon.ico")
        or path.startswith("/static/")
    ):
        return await call_next(request)

    session_id = request.cookies.get("session")
    sess = get_session(session_id)
    if not sess:
        return RedirectResponse(url="/auth", status_code=302)

    # CSRF-защита для небезопасных методов (HTML-формы)
    if request.method.upper() in {"POST", "PUT", "PATCH", "DELETE"}:
        # /logout — тоже защищаем (кнопка в UI отправляет GET сейчас, но на будущее)
        form_token = None
        header_token = request.headers.get("x-csrf-token")
        try:
            # starlette кэширует body, так что form() безопасен
            form = await request.form()
            form_token = form.get("csrf_token")
        except Exception:
            form_token = None
        if not (form_token and form_token == sess.csrf_token) and not (
            header_token and header_token == sess.csrf_token
        ):
            return Response(status_code=HTTP_403_FORBIDDEN, content="CSRF check failed")

    # Сохраняем данные пользователя в state для использования в шаблонах/роутах
    request.state.username = sess.username
    request.state.role = sess.role
    request.state.csrf_token = sess.csrf_token
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
    BACKEND_DIR = Path(__file__).resolve().parent
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        reload_dirs=[str(BACKEND_DIR)],
    )
