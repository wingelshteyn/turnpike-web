"""Менеджер токенов для авторизации в API axioma24."""

from __future__ import annotations

import asyncio
import base64
import logging
import time
from dataclasses import dataclass
from datetime import datetime, timezone

import httpx

from .config import HOST_AUTH, TOKEN_CACHE_TTL_SECONDS

logger = logging.getLogger(__name__)

@dataclass
class _TokenBundle:
    access: str
    refresh: str
    session: str
    obtained_at: float


_cache_lock = asyncio.Lock()
_token_cache: dict[tuple[str, str], _TokenBundle] = {}


def _now() -> float:
    return time.time()


class TokenManager:
    """Получает и обновляет токены доступа через API авторизации."""

    def __init__(self, username: str = "test", password: str = "test"):
        self.username = username
        self.password = password
        self.token_access: str | None = None
        self.token_refresh: str | None = None
        self.session: str | None = None

    # ------------------------------------------------------------------
    # Публичный интерфейс
    # ------------------------------------------------------------------

    async def authenticate(self) -> str:
        """Авторизация: получить токены и сессию."""
        cache_key = (self.username, self.password)

        async with _cache_lock:
            cached = _token_cache.get(cache_key)
            if cached and (_now() - cached.obtained_at) < TOKEN_CACHE_TTL_SECONDS:
                self.token_access = cached.access
                self.token_refresh = cached.refresh
                self.session = cached.session
                return self.token_access

        async with httpx.AsyncClient(timeout=10) as client:
            await self._obtain_tokens(client)
            await self._login(client)

        if not (self.token_access and self.token_refresh and self.session):
            raise RuntimeError("Токены/сессия не получены")

        async with _cache_lock:
            _token_cache[cache_key] = _TokenBundle(
                access=self.token_access,
                refresh=self.token_refresh,
                session=self.session,
                obtained_at=_now(),
            )
        return self.token_access

    @staticmethod
    def token_expire_ms(token: str) -> int:
        """Пытается достать expires/exp из JWT без верификации подписи."""
        try:
            parts = token.split(".")
            if len(parts) < 2:
                return 0
            payload_b64 = parts[1]
            payload_b64 += "=" * (-len(payload_b64) % 4)
            payload_json = base64.urlsafe_b64decode(payload_b64.encode("utf-8")).decode("utf-8")
            import json

            payload = json.loads(payload_json)
            v = payload.get("expires") or payload.get("exp")
            if not v:
                return 0
            # exp чаще всего seconds since epoch
            if isinstance(v, (int, float)):
                return int(v * 1000)
            # или строка-датавремя (ISO)
            if isinstance(v, str):
                try:
                    dt = datetime.fromisoformat(v.replace("Z", "+00:00"))
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=timezone.utc)
                    return int(dt.timestamp() * 1000)
                except Exception:
                    return 0
            return 0
        except Exception:
            return 0

    def get_auth_headers(self) -> dict:
        """Заголовки для авторизованных запросов."""
        headers = {
            "Authorization": f"Bearer {self.token_access}",
            "Content-Type": "application/json",
        }
        if self.session:
            headers["Cookie"] = f"session={self.session}"
        return headers

    async def refresh_tokens(self) -> None:
        """Обновить пару access/refresh токенов."""
        if not self.token_refresh:
            raise RuntimeError("Refresh token отсутствует")
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(
                f"{HOST_AUTH}/refresh",
                headers={"Authorization": f"Bearer {self.token_refresh}"},
            )
            if response.status_code != 200:
                raise RuntimeError("Не удалось обновить токены")

            data = response.json()
            if not data.get("success"):
                raise RuntimeError(f"Ошибка обновления токенов: {data.get('error')}")

            tokens = data.get("result", {})
            self.token_access = tokens.get("token_access")
            self.token_refresh = tokens.get("token_refresh")
            logger.info("Токены обновлены")

        if self.token_access and self.token_refresh and self.session:
            cache_key = (self.username, self.password)
            async with _cache_lock:
                _token_cache[cache_key] = _TokenBundle(
                    access=self.token_access,
                    refresh=self.token_refresh,
                    session=self.session,
                    obtained_at=_now(),
                )

    async def login_with_password(self, *, username: str, password: str) -> _TokenBundle:
        """Axioma flow: authorize (login/password) -> login (session cookie)."""
        self.username = username
        self.password = password
        async with httpx.AsyncClient(timeout=15) as client:
            await self._obtain_tokens(client)
            await self._login(client)
        if not (self.token_access and self.token_refresh and self.session):
            raise RuntimeError("Токены/сессия не получены")
        return _TokenBundle(
            access=self.token_access,
            refresh=self.token_refresh,
            session=self.session,
            obtained_at=_now(),
        )

    async def refresh_with_refresh_token(self, refresh_token: str) -> tuple[str, str]:
        """Обновить access/refresh по refresh_token (как в JS-примере)."""
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(
                f"{HOST_AUTH}/refresh",
                headers={"Authorization": f"Bearer {refresh_token}"},
            )
            response.raise_for_status()
            data = response.json()
            if not data.get("success"):
                raise RuntimeError(f"Ошибка обновления токенов: {data.get('error')}")
            tokens = data.get("result", {})
            access = tokens.get("token_access")
            refresh = tokens.get("token_refresh")
            if not access or not refresh:
                raise RuntimeError("Токены не получены при refresh")
            return access, refresh

    # ------------------------------------------------------------------
    # Внутренние методы
    # ------------------------------------------------------------------

    async def _obtain_tokens(self, client: httpx.AsyncClient) -> None:
        # В JS-примере используется application/x-www-form-urlencoded
        response = await client.post(
            f"{HOST_AUTH}/authorize",
            data={"login": self.username, "password": self.password},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        if response.status_code != 200:
            raise RuntimeError(f"Не удалось авторизоваться: {response.text}")

        data = response.json()
        if not data.get("success"):
            raise RuntimeError(f"Ошибка авторизации: {data.get('error', 'unknown')}")

        tokens = data.get("result", {})
        self.token_access = tokens.get("token_access")
        self.token_refresh = tokens.get("token_refresh")

        if not self.token_access or not self.token_refresh:
            raise RuntimeError("Токены не получены")
        logger.info("Токены получены")

    async def _login(self, client: httpx.AsyncClient) -> None:
        response = await client.get(
            f"{HOST_AUTH}/login",
            headers={"Authorization": f"Bearer {self.token_access}"},
        )
        if response.status_code != 200:
            raise RuntimeError(f"Ошибка входа: {response.text}")

        data = response.json()
        if not data.get("success"):
            raise RuntimeError(f"Ошибка входа: {data.get('error', 'unknown')}")

        self._extract_session(response)
        if not self.session:
            raise RuntimeError("Сессия не получена")
        logger.info("Сессия получена")

    def _extract_session(self, response: httpx.Response) -> None:
        self.session = response.cookies.get("session")
        if self.session:
            return
        set_cookie = response.headers.get("set-cookie", "")
        for part in set_cookie.split(";"):
            if part.strip().startswith("session="):
                self.session = part.strip().split("=", 1)[1]
                return
