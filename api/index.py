"""
Vercel Serverless Function entrypoint.

Vercel ожидает Python handler внутри директории `api/`.
Мы экспортируем ASGI-приложение FastAPI как `app`.
"""

from backend.main import app  # noqa: F401

