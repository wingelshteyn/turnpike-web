"""Общие CRUD-операции для сущностей с полями Brief и Name (PartnerType, RegionType)."""

from __future__ import annotations

from typing import Any, Dict, Optional


class BriefNameCRUDMixin:
    """Миксин для API-классов с create/update/delete по схеме Brief/Name."""

    async def create(self, brief: str, name: str) -> Dict[str, Any]:
        payload = {"Brief": brief, "Name": name}
        return (await self._request("POST", "create", json=payload))[0]

    async def update(self, record_id: int, brief: str, name: str) -> Dict[str, Any]:
        payload = {"id": record_id, "Brief": brief, "Name": name}
        return (await self._request("PUT", "update", json=payload))[0]

    async def delete(self, record_id: int, user_id: Optional[int] = None) -> Dict[str, Any]:
        payload: Dict[str, Any] = {"id": record_id}
        if user_id is not None:
            payload["f_user"] = user_id
        return (await self._request("DELETE", "delete", json=payload))[0]
