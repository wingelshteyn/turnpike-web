"""API-клиент для территорий (axgate.Region)."""

from __future__ import annotations

from typing import Any, Dict

from ..config import API_BASE_URL
from .base import BaseAPI


class RegionAPI(BaseAPI):
    def __init__(self):
        super().__init__(base_url=f"{API_BASE_URL}/axgate.Region")

    async def create(
        self, partner: int, region_type: int, name: str, place: str,
    ) -> Dict[str, Any]:
        payload = {
            "partner": partner,
            "regiontype": region_type,
            "name": name,
            "place": place,
        }
        return (await self._request("POST", "create", json=payload))[0]

    async def update(
        self,
        record_id: int,
        partner: int,
        region_type: int,
        name: str,
        place: str,
    ) -> Dict[str, Any]:
        payload = {
            "id": record_id,
            "partner": partner,
            "regiontype": region_type,
            "name": name,
            "place": place,
        }
        return (await self._request("PUT", "update", json=payload))[0]
