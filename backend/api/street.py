"""API-клиент для улиц (axgate.Street).

Автоматически нормализует поле ``city`` → ``City`` в ответах API.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from ..config import API_BASE_URL
from .base import BaseAPI

logger = logging.getLogger(__name__)


class StreetAPI(BaseAPI):
    """API улиц с автоматической нормализацией поля city → City."""

    def __init__(self):
        super().__init__(base_url=f"{API_BASE_URL}/axgate.Street")

    # ------------------------------------------------------------------
    # Нормализация: city → City
    # ------------------------------------------------------------------

    async def _request(self, method, action, **kwargs):
        result = await super()._request(method, action, **kwargs)
        for row in result:
            if "city" in row and "City" not in row:
                row["City"] = row.pop("city")
        return result

    # ------------------------------------------------------------------
    # Переопределённые методы
    # ------------------------------------------------------------------

    async def list(
        self, limit: int | None = None, include_deleted: bool = False,
    ) -> List[Dict[str, Any]]:
        params: Dict[str, Any] = {}
        if limit is not None:
            params["limit"] = limit
        params["include_deleted"] = "true" if include_deleted else "false"
        response = await self._request("GET", "list", params=params)
        logger.debug("StreetAPI.list response: %s", response)
        if not include_deleted:
            response = [row for row in response if not row.get("deleted")]
        return response

    async def create(self, city: int, name: str) -> Dict[str, Any]:
        payload = {"city": city, "name": name}
        return (await self._request("POST", "create", json=payload))[0]

    async def update(self, record_id: int, city: int, name: str) -> Dict[str, Any]:
        payload = {"id": record_id, "city": city, "name": name}
        return (await self._request("PUT", "update", json=payload))[0]
