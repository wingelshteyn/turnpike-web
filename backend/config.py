"""Конфигурация приложения: URL-адреса API, константы."""

from pathlib import Path

HOST_AUTH = "https://apiarm.axioma24.ru/auth"
API_BASE_URL = "https://apiarm.axioma24.ru"

# Абсолютный путь к шаблонам, вычисляется от расположения этого файла
BACKEND_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = str(BACKEND_DIR / "templates")
STATIC_DIR = str(BACKEND_DIR / "static")
