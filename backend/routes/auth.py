"""Маршруты авторизации."""

import logging
import secrets

from fastapi import APIRouter, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse

from dependencies import templates
from token_manager import TokenManager
from user_store import authenticate as local_authenticate

logger = logging.getLogger(__name__)

router = APIRouter(tags=["auth"])


def _set_auth_cookies(response, username: str, session_value: str, access_token: str = ""):
    """Установить куки авторизации."""
    max_age = 3600 * 24  # 24 часа
    response.set_cookie(key="session", value=session_value, httponly=True, max_age=max_age)
    if access_token:
        response.set_cookie(key="access_token", value=access_token, httponly=True, max_age=max_age)
    response.set_cookie(key="username", value=username, max_age=max_age)


@router.get("/auth", response_class=HTMLResponse)
async def auth_form(request: Request):
    """Страница авторизации."""
    session = request.cookies.get("session")
    if session:
        return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse("auth.html", {"request": request})


@router.post("/auth", response_class=HTMLResponse)
async def auth_login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
):
    """Обработка формы входа: сначала локальная БД, потом внешний API."""

    # --- 1. Проверяем локальное хранилище пользователей ---
    local_user = local_authenticate(username, password)
    if local_user:
        response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
        # Генерируем локальную сессию
        session_token = secrets.token_hex(32)
        _set_auth_cookies(response, username, session_token)
        logger.info("Локальный пользователь %s авторизован (роль: %s)", username, local_user["role"])
        return response

    # --- 2. Внешний API (axioma24) ---
    try:
        token_manager = TokenManager(username=username, password=password)
        await token_manager.authenticate()

        response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
        _set_auth_cookies(
            response,
            username,
            token_manager.session or secrets.token_hex(32),
            token_manager.token_access or "",
        )
        logger.info("Пользователь %s авторизован через внешний API", username)
        return response

    except RuntimeError as e:
        logger.error("Ошибка авторизации: %s", str(e))
        return templates.TemplateResponse(
            "auth.html",
            {"request": request, "error": "Неверное имя пользователя или пароль"},
        )


@router.get("/logout")
async def logout():
    """Выход из системы — удаление куки и редирект на страницу авторизации."""
    response = RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)
    response.delete_cookie("session")
    response.delete_cookie("access_token")
    response.delete_cookie("username")
    logger.info("Пользователь вышел из системы")
    return response
