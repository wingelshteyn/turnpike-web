"""Общие зависимости приложения (templates и пр.)."""

from typing import Any

from fastapi import Request
from fastapi.templating import Jinja2Templates

from .config import TEMPLATES_DIR

templates = Jinja2Templates(directory=TEMPLATES_DIR)
templates.env.globals["range"] = range


def template_ctx(request: Request, **kwargs: Any) -> dict[str, Any]:
    """Единый контекст для HTML-шаблонов: request, username из сессии, доп. поля."""
    ctx: dict[str, Any] = {
        "request": request,
        "username": getattr(request.state, "username", None),
    }
    ctx.update(kwargs)
    return ctx