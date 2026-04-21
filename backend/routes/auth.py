"""Маршруты авторизации."""

import logging

from fastapi import APIRouter, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse

from ..dependencies import templates
from ..url_prefix import redirect as prefixed_redirect
from ..token_manager import TokenManager
from ..user_store import authenticate as local_authenticate
from ..session_store import create_session, delete_session, get_session
from ..config import COOKIE_SAMESITE, COOKIE_SECURE

logger = logging.getLogger(__name__)

router = APIRouter(tags=["auth"])


def _set_session_cookie(response, session_id: str):
    """Установить cookie с id серверной сессии."""
    max_age = 3600 * 24  # 24 часа
    response.set_cookie(
        key="session",
        value=session_id,
        httponly=True,
        max_age=max_age,
        samesite=COOKIE_SAMESITE,
        secure=COOKIE_SECURE,
    )


@router.get("/", response_class=HTMLResponse)
async def auth_form(request: Request):
    """Страница авторизации."""
    session_id = request.cookies.get("session")
    if get_session(session_id):
        return prefixed_redirect(request, "/analytics", status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse("auth.html", {"request": request})


@router.post("/", response_class=HTMLResponse)
async def auth_login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
):
    """Обработка формы входа: сначала локальная БД, потом внешний API."""

    # --- 1. Проверяем локальное хранилище пользователей ---
    local_user = local_authenticate(username, password)
    if local_user:
        response = prefixed_redirect(request, "/analytics", status_code=status.HTTP_303_SEE_OTHER)
        sess = create_session(username=local_user["username"], role=local_user["role"])
        _set_session_cookie(response, sess.session_id)
        logger.info("Локальный пользователь %s авторизован (роль: %s)", username, local_user["role"])
        return response

    # --- 2. Внешний API (axioma24) ---
    try:
        token_manager = TokenManager(username=username, password=password)
        await token_manager.authenticate()

        response = prefixed_redirect(request, "/analytics", status_code=status.HTTP_303_SEE_OTHER)
        # Создаём серверную сессию (username/role тут минимальные)
        sess = create_session(username=username, role="USER")
        _set_session_cookie(response, sess.session_id)
        logger.info("Пользователь %s авторизован через внешний API", username)
        return response

    except RuntimeError as e:
        logger.error("Ошибка авторизации: %s", str(e))
        return templates.TemplateResponse(
            "auth.html",
            {"request": request, "error": "Неверное имя пользователя или пароль"},
        )


@router.get("/logout")
async def logout(request: Request):
    """Выход из системы — удаление куки и редирект на страницу авторизации."""
    response = prefixed_redirect(request, "/", status_code=status.HTTP_302_FOUND)
    delete_session(request.cookies.get("session"))
    response.delete_cookie("session")
    logger.info("Пользователь вышел из системы")
    return response
