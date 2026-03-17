"""API-клиент для типов контактов (axgate.ContactType)."""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from config import API_BASE_URL
from api.base import BaseAPI

logger = logging.getLogger(__name__)


class ContactTypeAPI(BaseAPI):
    def __init__(self):
        super().__init__(base_url=f"{API_BASE_URL}/axgate.ContactType")

    async def list(
        self, limit: int | None = None, include_deleted: bool = False,
    ) -> List[Dict[str, Any]]:
        params: Dict[str, Any] = {}
        if limit is not None:
            params["limit"] = limit
        params["include_deleted"] = "true" if include_deleted else "false"
        return await self._request("GET", "list", params=params)

    async def create(self, code: str = "", name: str = "") -> Dict[str, Any]:
        payload: Dict[str, Any] = {}
        if code:
            payload["Code"] = code
        if name:
            payload["Name"] = name
        return (await self._request("POST", "create", json=payload))[0]

    async def update(self, record_id: int, code: str = "", name: str = "") -> Dict[str, Any]:
        payload: Dict[str, Any] = {"id": record_id}
        if code is not None:
            payload["Code"] = code
        if name is not None:
            payload["Name"] = name
        return (await self._request("PUT", "update", json=payload))[0]
