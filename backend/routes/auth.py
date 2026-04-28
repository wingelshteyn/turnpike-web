"""Маршруты авторизации."""

import logging
import time

from fastapi import APIRouter, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse

from ..dependencies import templates
from ..url_prefix import redirect as prefixed_redirect
from ..token_manager import TokenManager
from ..session_store import create_session, delete_session, get_session, update_session_auth
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
    # Vercel: cookie-based session via SessionMiddleware
    if "session" in request.scope and request.session.get("username"):
        return prefixed_redirect(request, "/analytics", status_code=status.HTTP_302_FOUND)

    session_id = request.cookies.get("session")
    if session_id and get_session(session_id):
        return prefixed_redirect(request, "/analytics", status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse(request, "auth.html", {"error": None})


@router.post("/", response_class=HTMLResponse)
async def auth_login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
):
    """Вход через внешний API (axioma24) по примеру JS."""
    try:
        tm = TokenManager()
        bundle = await tm.login_with_password(username=username, password=password)
        saved_at_ms = int(time.time() * 1000)

        response = prefixed_redirect(request, "/analytics", status_code=status.HTTP_303_SEE_OTHER)
        if "session" in request.scope:
            request.session.update({
                "username": username,
                "role": "USER",
                "csrf_token": "csrf",
                "token_access": bundle.access,
                "token_refresh": bundle.refresh,
                "axioma_session": bundle.session,
                "saved_at_ms": saved_at_ms,
            })
        else:
            sess = create_session(
                username=username,
                role="USER",
                token_access=bundle.access,
                token_refresh=bundle.refresh,
                axioma_session=bundle.session,
                saved_at_ms=saved_at_ms,
            )
            _set_session_cookie(response, sess.session_id)
        logger.info("Пользователь %s авторизован через внешний API", username)
        return response

    except RuntimeError as e:
        logger.error("Ошибка авторизации: %s", str(e))
        return templates.TemplateResponse(
            request,
            "auth.html",
            {"error": "Неверное имя пользователя или пароль"},
        )


@router.get("/logout")
async def logout(request: Request):
    """Выход из системы — удаление куки и редирект на страницу авторизации."""
    response = prefixed_redirect(request, "/", status_code=status.HTTP_302_FOUND)
    if "session" in request.scope:
        request.session.clear()
    delete_session(request.cookies.get("session"))
    response.delete_cookie("session")
    logger.info("Пользователь вышел из системы")
    return response
