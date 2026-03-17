"""Менеджер токенов для авторизации в API axioma24."""

from __future__ import annotations

import logging

import httpx

from config import HOST_AUTH

logger = logging.getLogger(__name__)


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
        async with httpx.AsyncClient() as client:
            await self._obtain_tokens(client)
            await self._login(client)
        return self.token_access

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
        async with httpx.AsyncClient() as client:
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

    # ------------------------------------------------------------------
    # Внутренние методы
    # ------------------------------------------------------------------

    async def _obtain_tokens(self, client: httpx.AsyncClient) -> None:
        response = await client.post(
            f"{HOST_AUTH}/authorize",
            json={"login": self.username, "password": self.password},
            headers={"Content-Type": "application/json"},
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
