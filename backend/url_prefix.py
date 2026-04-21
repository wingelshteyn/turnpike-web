"""Утилиты для работы с префиксом приложения за reverse-proxy.

Когда FastAPI запущен за nginx на подпути (например, /gui/gate/), nginx обычно
проксирует запросы на backend, "срезая" префикс. В этом случае backend видит пути
вида /static/... и /, но пользователю нужно выдавать ссылки и редиректы с
префиксом. Для этого nginx должен передавать заголовок X-Forwarded-Prefix.
"""

from __future__ import annotations

from fastapi import Request
from starlette.responses import RedirectResponse


def normalize_prefix(prefix: str | None) -> str:
    if not prefix:
        return ""
    prefix = prefix.strip()
    if not prefix:
        return ""
    if not prefix.startswith("/"):
        prefix = "/" + prefix
    # "/gui/gate/" -> "/gui/gate"
    if len(prefix) > 1:
        prefix = prefix.rstrip("/")
    return prefix


def get_root_path(request: Request) -> str:
    """Возвращает нормализованный префикс приложения для текущего запроса."""
    hdr_prefix = request.headers.get("x-forwarded-prefix")
    if hdr_prefix:
        return normalize_prefix(hdr_prefix)
    return normalize_prefix(request.scope.get("root_path"))


def with_root_path(request: Request, path: str) -> str:
    """Добавляет root_path к абсолютному пути (например, '/auth')."""
    if not path:
        return get_root_path(request) or "/"
    # Внешние URL не трогаем
    if "://" in path:
        return path
    if not path.startswith("/"):
        path = "/" + path
    root = get_root_path(request)
    if not root:
        return path
    if path == "/":
        return root + "/"
    return root + path


def redirect(request: Request, path: str, status_code: int = 302) -> RedirectResponse:
    return RedirectResponse(url=with_root_path(request, path), status_code=status_code)

