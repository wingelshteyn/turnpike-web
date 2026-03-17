"""Локальное хранилище пользователей (JSON-файл)."""

from __future__ import annotations

import hashlib
import json
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

_USERS_FILE = Path(__file__).resolve().parent / "users.json"


def _hash_password(password: str) -> str:
    """SHA-256 хэш пароля."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def _load() -> dict:
    if _USERS_FILE.exists():
        return json.loads(_USERS_FILE.read_text("utf-8"))
    return {}


def _save(data: dict) -> None:
    _USERS_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), "utf-8")


# ------------------------------------------------------------------
# Публичный интерфейс
# ------------------------------------------------------------------

def init_users() -> None:
    """Инициализация: создать администратора по умолчанию, если его ещё нет."""
    users = _load()
    if "admin" not in users:
        users["admin"] = {
            "password": _hash_password("admin"),
            "role": "ADMIN",
        }
        _save(users)
        logger.info("Создан администратор по умолчанию (admin / admin)")
    else:
        logger.info("Администратор уже существует")


def authenticate(username: str, password: str) -> Optional[dict]:
    """Проверить локальные учётные данные.

    Возвращает ``{"username": ..., "role": ...}`` при успехе, иначе ``None``.
    """
    users = _load()
    user = users.get(username)
    if user and user["password"] == _hash_password(password):
        return {"username": username, "role": user["role"]}
    return None


def create_user(username: str, password: str, role: str = "USER") -> bool:
    """Создать нового пользователя. Возвращает True при успехе."""
    users = _load()
    if username in users:
        return False
    users[username] = {
        "password": _hash_password(password),
        "role": role,
    }
    _save(users)
    logger.info("Создан пользователь %s (роль: %s)", username, role)
    return True
