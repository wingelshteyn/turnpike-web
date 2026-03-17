"""API-клиент для клиентов (axgate.Client)."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from config import API_BASE_URL
from api.base import BaseAPI

logger = logging.getLogger(__name__)


class ClientAPI(BaseAPI):
    def __init__(self):
        super().__init__(base_url=f"{API_BASE_URL}/axgate.Client")

    async def list(
        self, limit: int | None = None, include_deleted: bool = False,
    ) -> List[Dict[str, Any]]:
        params: Dict[str, Any] = {}
        if limit is not None:
            params["limit"] = limit
        params["include_deleted"] = "true" if include_deleted else "false"
        return await self._request("GET", "list", params=params)

    async def create(
        self,
        name: str = "",
        place: str = "",
        house: Optional[int] = None,
        apart: Optional[str] = None,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {}
        if name:
            payload["Name"] = name
        if place:
            payload["Place"] = place
        if house is not None:
            payload["House"] = house
        if apart:
            payload["Apart"] = apart
        return (await self._request("POST", "create", json=payload))[0]

    async def update(
        self,
        record_id: int,
        name: str = "",
        place: str = "",
        house: Optional[int] = None,
        apart: Optional[str] = None,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {"id": record_id}
        if name is not None:
            payload["Name"] = name
        if place is not None:
            payload["Place"] = place
        if house is not None:
            payload["House"] = house
        if apart is not None:
            payload["Apart"] = apart
        return (await self._request("PUT", "update", json=payload))[0]
