"""Локальное хранилище пользователей (JSON-файл)."""

from __future__ import annotations

import json
import logging
from typing import Optional

import bcrypt

from .config import DATA_DIR

logger = logging.getLogger(__name__)

_USERS_FILE = DATA_DIR / "users.json"


def _hash_password(password: str) -> str:
    """Безопасный хэш пароля (bcrypt)."""
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def _verify_password(password: str, stored_hash: str) -> bool:
    """Проверка пароля.

    Поддерживает:
    - bcrypt-хэши (новый формат)
    - legacy SHA-256 hex (старый формат) — для миграции при первом логине
    """
    if not stored_hash:
        return False
    # bcrypt
    if stored_hash.startswith("$2"):
        try:
            return bcrypt.checkpw(password.encode("utf-8"), stored_hash.encode("utf-8"))
        except Exception:
            return False
    # legacy sha256 hex (64 символа)
    if len(stored_hash) == 64:
        import hashlib

        legacy = hashlib.sha256(password.encode("utf-8")).hexdigest()
        return legacy == stored_hash
    return False


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
    if not user:
        return None
    stored = user.get("password", "")
    if _verify_password(password, stored):
        # миграция legacy sha256 → bcrypt при первом успешном входе
        if stored and len(stored) == 64 and not stored.startswith("$2"):
            user["password"] = _hash_password(password)
            users[username] = user
            _save(users)
        return {"username": username, "role": user.get("role", "USER")}
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
