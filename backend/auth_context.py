"""Auth context for the current request.

Хранит токены/сессию Axioma для текущего запроса, чтобы API-клиенты могли
брать авторизационные заголовки без прокидывания параметров по всем роутам.
"""

from __future__ import annotations

from contextvars import ContextVar
from dataclasses import dataclass
from typing import Awaitable, Callable, Optional


@dataclass
class AuthBundle:
    username: str
    role: str
    token_access: str
    token_refresh: str
    axioma_session: str
    saved_at_ms: int


@dataclass
class AuthContext:
    bundle: AuthBundle
    # Сохранить обновлённые токены/сессию в backing store (cookie session / session_store)
    persist: Callable[[AuthBundle], Awaitable[None]]


_CTX: ContextVar[AuthContext | None] = ContextVar("turnpike_auth_ctx", default=None)


def set_auth_context(ctx: AuthContext) -> object:
    return _CTX.set(ctx)


def reset_auth_context(token: object) -> None:
    _CTX.reset(token)


def get_auth_context() -> Optional[AuthContext]:
    return _CTX.get()

