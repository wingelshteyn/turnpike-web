"""API-клиент для партнёров (axgate.Partner)."""

from __future__ import annotations

from typing import Any, Dict

from config import API_BASE_URL
from api.base import BaseAPI


class PartnerAPI(BaseAPI):
    def __init__(self):
        super().__init__(base_url=f"{API_BASE_URL}/axgate.Partner")

    async def create(self, partner_type: int, name: str) -> Dict[str, Any]:
        payload = {"f_PartnerType": partner_type, "Name": name}
        return (await self._request("POST", "create", json=payload))[0]

    async def update(
        self, record_id: int, partner_type: int, name: str,
    ) -> Dict[str, Any]:
        payload = {"id": record_id, "f_PartnerType": partner_type, "Name": name}
        return (await self._request("PUT", "update", json=payload))[0]
