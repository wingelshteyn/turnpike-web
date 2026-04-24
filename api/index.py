"""
Vercel Serverless Function entrypoint.

Vercel ожидает ASGI/WSGI приложение верхнего уровня с именем `app`
в одном из entrypoint'ов (в т.ч. `api/index.py`).
"""

from __future__ import annotations

import traceback

from fastapi import FastAPI
from fastapi.responses import PlainTextResponse


app = FastAPI()

try:
    from backend.main import app as backend_app  # type: ignore

    # Важно: оставляем top-level `app` (для детектора Vercel),
    # а настоящее приложение монтируем внутрь.
    app.mount("/", backend_app)
except Exception as exc:  # pragma: no cover
    # Важно: если импорт упал, Vercel иначе просто покажет FUNCTION_INVOCATION_FAILED.
    # Делаем минимальный app, который вернёт traceback (для диагностики).
    _err = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))

    @app.get("/health", include_in_schema=False)
    @app.get("/__vercel_error", include_in_schema=False)
    async def __vercel_error():
        return PlainTextResponse(_err, status_code=500)

