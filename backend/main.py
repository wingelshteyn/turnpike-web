"""Точка входа приложения: создание FastAPI-приложения и подключение маршрутов."""

import logging
from pathlib import Path

import uvicorn
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import RedirectResponse, Response
from starlette.status import HTTP_403_FORBIDDEN

import os

from .config import STATIC_DIR, SESSION_SECRET
from .url_prefix import normalize_prefix, redirect as prefixed_redirect
from .session_store import get_session, init_session_store
from .routes import (
    analytics_pages_router,
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

# --- Env flags ---
_is_vercel = bool(os.environ.get("VERCEL_ENV")) or (os.environ.get("VERCEL") == "1")

# --- Middleware: учёт префикса reverse-proxy (nginx) ---
@app.middleware("http")
async def forwarded_prefix_middleware(request: Request, call_next):
    """
    Если nginx публикует приложение на подпути (например, /gui/gate/),
    он должен передавать X-Forwarded-Prefix: /gui/gate.

    Тогда `url_for()` в шаблонах и редиректы смогут корректно формировать URL.
    """
    prefix = request.headers.get("x-forwarded-prefix")
    if prefix:
        request.scope["root_path"] = normalize_prefix(prefix)
    return await call_next(request)


# --- Статические файлы ---
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


# --- Middleware: проверка аутентификации ---
@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    """Проверяет валидность сессии. Без авторизации доступна только / и статика."""
    path = request.url.path

    # Разрешаем доступ без авторизации
    if (
        path in ("/", "/favicon.ico", "/health")
        or path.startswith("/static/")
    ):
        return await call_next(request)

    if _is_vercel and "session" in request.scope:
        # На Vercel используем cookie-based сессии (request.session)
        sess = request.session or {}
        if not sess.get("username"):
            return prefixed_redirect(request, "/", status_code=302)
        request.state.username = sess.get("username")
        request.state.role = sess.get("role", "USER")
        request.state.csrf_token = sess.get("csrf_token", "")
        return await call_next(request)

    session_id = request.cookies.get("session")
    sess = get_session(session_id)
    if not sess:
        return prefixed_redirect(request, "/", status_code=302)

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


# --- Cookie-based sessions for Vercel (stateless) ---
# Важно: добавляем SessionMiddleware ПОСЛЕ декларативных @app.middleware,
# чтобы она оборачивала их и успевала проставить `scope['session']`.
if _is_vercel:
    app.add_middleware(
        SessionMiddleware,
        secret_key=SESSION_SECRET,
        same_site="lax",
        https_only=True,
    )


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
app.include_router(analytics_pages_router)


@app.get("/health", include_in_schema=False)
async def health():
    """Проверка готовности для балансировщика / оркестратора."""
    return {"status": "ok"}


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
