"""Простое серверное хранилище сессий.

В этом проекте используется server-rendered HTML + cookie-based session id.
Сессионные данные (username/role/csrf) хранятся на сервере и валидируются.
"""

from __future__ import annotations

import json
import secrets
import threading
import time
from dataclasses import dataclass, asdict
from typing import Optional

from .config import DATA_DIR


@dataclass
class SessionData:
    session_id: str
    username: str
    role: str
    csrf_token: str
    created_at: float
    expires_at: float


_SESSIONS_FILE = DATA_DIR / "sessions.json"

_lock = threading.RLock()
_sessions: dict[str, SessionData] = {}


def _now() -> float:
    return time.time()


def _load_from_disk() -> None:
    if not _SESSIONS_FILE.exists():
        return
    try:
        raw = json.loads(_SESSIONS_FILE.read_text("utf-8"))
        if not isinstance(raw, dict):
            return
        for sid, payload in raw.items():
            if not isinstance(payload, dict):
                continue
            try:
                _sessions[sid] = SessionData(**payload)
            except TypeError:
                continue
    except Exception:
        return


def _save_to_disk() -> None:
    data = {sid: asdict(sess) for sid, sess in _sessions.items()}
    try:
        _SESSIONS_FILE.parent.mkdir(parents=True, exist_ok=True)
        _SESSIONS_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), "utf-8")
    except Exception:
        # best-effort: на serverless FS запись может быть недоступна
        return


def init_session_store() -> None:
    """Загрузить сессии с диска (best-effort)."""
    with _lock:
        _load_from_disk()
        cleanup_expired(save=False)


def create_session(username: str, role: str, ttl_seconds: int = 3600 * 24) -> SessionData:
    now = _now()
    sid = secrets.token_urlsafe(32)
    csrf = secrets.token_urlsafe(32)
    sess = SessionData(
        session_id=sid,
        username=username,
        role=role,
        csrf_token=csrf,
        created_at=now,
        expires_at=now + ttl_seconds,
    )
    with _lock:
        _sessions[sid] = sess
        _save_to_disk()
    return sess


def get_session(session_id: str | None) -> Optional[SessionData]:
    if not session_id:
        return None
    with _lock:
        sess = _sessions.get(session_id)
        if not sess:
            return None
        if sess.expires_at <= _now():
            _sessions.pop(session_id, None)
            _save_to_disk()
            return None
        return sess


def delete_session(session_id: str | None) -> None:
    if not session_id:
        return
    with _lock:
        if session_id in _sessions:
            _sessions.pop(session_id, None)
            _save_to_disk()


def cleanup_expired(*, save: bool = True) -> int:
    """Удалить протухшие сессии. Возвращает количество удалённых."""
    now = _now()
    removed = 0
    with _lock:
        expired = [sid for sid, sess in _sessions.items() if sess.expires_at <= now]
        for sid in expired:
            _sessions.pop(sid, None)
            removed += 1
        if removed and save:
            _save_to_disk()
    return removed

