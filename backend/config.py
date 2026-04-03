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
DATA_DIR = Path(_data_dir_env).resolve() if _data_dir_env else BACKEND_DIR
TEMPLATES_DIR = str(BACKEND_DIR / "templates")
STATIC_DIR = str(BACKEND_DIR / "static")
