"""API-клиент для контактов (axgate.Contact)."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from config import API_BASE_URL
from api.base import BaseAPI

logger = logging.getLogger(__name__)


class ContactAPI(BaseAPI):
    def __init__(self):
        super().__init__(base_url=f"{API_BASE_URL}/axgate.Contact")

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
        client_id: int = 0,
        contact_type_id: int = 0,
        contact: str = "",
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {}
        if client_id:
            payload["Client"] = client_id
        if contact_type_id:
            payload["ContactType"] = contact_type_id
        if contact:
            payload["Contact"] = contact
        return (await self._request("POST", "create", json=payload))[0]

    async def update(
        self,
        record_id: int,
        client_id: Optional[int] = None,
        contact_type_id: Optional[int] = None,
        contact: Optional[str] = None,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {"id": record_id}
        if client_id is not None:
            payload["Client"] = client_id
        if contact_type_id is not None:
            payload["ContactType"] = contact_type_id
        if contact is not None:
            payload["Contact"] = contact
        return (await self._request("PUT", "update", json=payload))[0]
