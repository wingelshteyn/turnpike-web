"""API-клиент для городов (axgate.City)."""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from ..config import API_BASE_URL
from .base import BaseAPI

logger = logging.getLogger(__name__)


class CityAPI(BaseAPI):
    def __init__(self):
        super().__init__(base_url=f"{API_BASE_URL}/axgate.City")

    async def list(
        self, limit: int | None = None, include_deleted: bool = False,
    ) -> List[Dict[str, Any]]:
        params: Dict[str, Any] = {}
        if limit is not None:
            params["limit"] = limit
        params["include_deleted"] = "true" if include_deleted else "false"
        response = await self._request("GET", "list", params=params)
        logger.debug("CityAPI.list response: %s", response)
        return response

    async def create(self, name: str) -> Dict[str, Any]:
        return (await self._request("POST", "create", json={"name": name}))[0]

    async def update(self, record_id: int, name: str) -> Dict[str, Any]:
        payload = {"id": record_id, "name": name}
        return (await self._request("PUT", "update", json=payload))[0]
