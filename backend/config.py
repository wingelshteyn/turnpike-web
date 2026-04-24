"""Конфигурация приложения: URL-адреса API, константы."""

import os
from pathlib import Path

HOST_AUTH = os.environ.get("HOST_AUTH", "https://apiarm.axioma24.ru/auth")
API_BASE_URL = os.environ.get("API_BASE_URL", "https://apiarm.axioma24.ru")

TOKEN_CACHE_TTL_SECONDS = int(os.environ.get("TOKEN_CACHE_TTL_SECONDS", "600"))

# в проде на HTTPS COOKIE_SECURE=true
COOKIE_SECURE = os.environ.get("COOKIE_SECURE", "false").lower() in ("1", "true", "yes", "on")
COOKIE_SAMESITE = os.environ.get("COOKIE_SAMESITE", "lax")

# Абсолютный путь к шаблонам, вычисляется от расположения этого файла
BACKEND_DIR = Path(__file__).resolve().parent
# Пользователи и сессии (JSON): по умолчанию рядом с кодом; в Docker задайте TURNPIKE_DATA_DIR=/data и смонтируйте том
_data_dir_env = os.environ.get("TURNPIKE_DATA_DIR")

# Vercel (serverless) имеет read-only файловую систему проекта.
# Для JSON-хранилищ используем /tmp (временный, но writable).
_is_vercel = os.environ.get("VERCEL") == "1" or bool(os.environ.get("VERCEL_ENV"))
if _data_dir_env:
    DATA_DIR = Path(_data_dir_env).resolve()
elif _is_vercel:
    DATA_DIR = Path("/tmp/turnpike_data")
else:
    DATA_DIR = BACKEND_DIR

# best-effort: гарантируем существование каталога
try:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
except Exception:
    # если каталог создать нельзя — пусть приложение решает на уровне store
    pass

TEMPLATES_DIR = str(BACKEND_DIR / "templates")
STATIC_DIR = str(BACKEND_DIR / "static")
