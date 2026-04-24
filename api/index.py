"""
Vercel Serverless Function entrypoint.

Vercel ожидает ASGI/WSGI приложение верхнего уровня с именем `app`
в одном из entrypoint'ов (в т.ч. `api/index.py`).
"""

from __future__ import annotations

import traceback

from fastapi import FastAPI
from fastapi import Request
from fastapi.responses import PlainTextResponse


app = FastAPI()
_LAST_ERR = ""


@app.get("/__vercel_error", include_in_schema=False)
@app.get("/__vercel_error/", include_in_schema=False)
async def __vercel_error_route():
    if _LAST_ERR:
        return PlainTextResponse(_LAST_ERR, status_code=500)
    return PlainTextResponse("no error captured (yet)", status_code=200)


@app.get("/health", include_in_schema=False)
async def __health():
    return {"status": "ok"}


@app.middleware("http")
async def __capture_exceptions(request: Request, call_next):
    global _LAST_ERR
    try:
        return await call_next(request)
    except Exception as exc:  # pragma: no cover
        _LAST_ERR = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
        # Не раскрываем traceback на обычных URL
        return PlainTextResponse("Internal Server Error", status_code=500)

try:
    from backend.main import app as backend_app  # type: ignore

    # Важно: оставляем top-level `app` (для детектора Vercel),
    # а настоящее приложение монтируем внутрь.
    app.mount("/", backend_app)
except Exception as exc:  # pragma: no cover
    # Важно: если импорт упал, Vercel иначе просто покажет FUNCTION_INVOCATION_FAILED.
    # Делаем минимальный app, который вернёт traceback (для диагностики).
    _LAST_ERR = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))

