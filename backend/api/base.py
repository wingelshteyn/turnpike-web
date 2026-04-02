"""Базовый API-клиент с общей логикой запросов."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import httpx
from fastapi import HTTPException

from ..token_manager import TokenManager

logger = logging.getLogger(__name__)


class BaseAPI:
    """Базовый клиент для работы с API axgate.

    Используется как контекстный менеджер::

        async with SomeAPI() as api:
            data = await api.list()
    """

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.token_manager = TokenManager()
        self.client: httpx.AsyncClient | None = None

    # ------------------------------------------------------------------
    # CRUD-операции
    # ------------------------------------------------------------------

    async def list(
        self, limit: int | None = None, include_deleted: bool = False,
    ) -> List[Dict[str, Any]]:
        params: Dict[str, Any] = {}
        if limit is not None:
            params["limit"] = limit
        if include_deleted:
            params["include_deleted"] = "true"
        return await self._request("GET", "list", params=params)

    async def case(self, limit: int | None = None) -> List[Dict[str, Any]]:
        params = {"limit": limit} if limit else None
        return await self._request("GET", "case", params=params)

    async def read(self, record_id: int) -> Dict[str, Any]:
        table = await self._request("GET", "read", params={"id": record_id})
        if not table:
            raise HTTPException(status_code=404, detail="Запись не найдена")
        return table[0]

    async def delete(self, record_id: int) -> Dict[str, Any]:
        return (await self._request("DELETE", "delete", json={"id": record_id}))[0]

    async def restore(self, record_id: int) -> Dict[str, Any]:
        return (await self._request("PUT", "restore", json={"id": record_id}))[0]

    # ------------------------------------------------------------------
    # Транспорт
    # ------------------------------------------------------------------

    async def _request(
        self,
        method: str,
        action: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/{action}"
        logger.debug("HTTP %s %s", method, url)

        try:
            response = await self.client.request(
                method, url, params=params, json=json,
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            # Один ретрай при 401/403: пытаемся обновить токены и повторить запрос
            if exc.response.status_code in (401, 403):
                try:
                    await self.token_manager.refresh_tokens()
                    await self.client.aclose()
                    self.client = httpx.AsyncClient(
                        headers=self.token_manager.get_auth_headers(),
                        timeout=10,
                    )
                    response = await self.client.request(
                        method, url, params=params, json=json,
                    )
                    response.raise_for_status()
                except Exception:
                    # если ретрай не помог — падаем в общий обработчик ниже
                    raise exc
        except httpx.TimeoutException as exc:
            logger.error("Таймаут при обращении к %s: %s", url, exc)
            raise HTTPException(
                status_code=504,
                detail="Внешний API не отвечает. Попробуйте позже.",
            ) from exc
        except httpx.ConnectError as exc:
            logger.error("Ошибка соединения с %s: %s", url, exc)
            raise HTTPException(
                status_code=502,
                detail="Не удалось подключиться к внешнему API.",
            ) from exc
        except httpx.HTTPStatusError as exc:
            logger.error(
                "Ошибка %s при обращении к %s: %s",
                exc.response.status_code, url, exc,
            )
            raise HTTPException(
                status_code=exc.response.status_code,
                detail=f"Ошибка внешнего API: {exc.response.text}",
            ) from exc

        payload = response.json()
        if not payload.get("success"):
            error_msg = payload.get("error", "Неизвестная ошибка API")
            logger.error("API вернул ошибку: %s", error_msg)
            raise HTTPException(
                status_code=500,
                detail=f"Внешний API вернул ошибку: {error_msg}",
            )

        result = payload.get("result", {}).get("Table", [])
        logger.debug("API response: %s", result)
        return result

    # ------------------------------------------------------------------
    # Контекстный менеджер
    # ------------------------------------------------------------------

    async def __aenter__(self):
        try:
            await self.token_manager.authenticate()
        except httpx.TimeoutException as exc:
            raise HTTPException(
                status_code=504,
                detail="Сервер авторизации не отвечает. Попробуйте позже.",
            ) from exc
        except httpx.ConnectError as exc:
            raise HTTPException(
                status_code=502,
                detail="Не удалось подключиться к серверу авторизации.",
            ) from exc
        self.client = httpx.AsyncClient(
            headers=self.token_manager.get_auth_headers(),
            timeout=10,
        )
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.client.aclose()
