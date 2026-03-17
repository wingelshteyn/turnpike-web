"""API-клиент для домов (axgate.House).

Автоматически нормализует поле ``street`` → ``Street`` в ответах API.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from config import API_BASE_URL
from api.base import BaseAPI

logger = logging.getLogger(__name__)


class HouseAPI(BaseAPI):
    """API домов с автоматической нормализацией поля street → Street."""

    def __init__(self):
        super().__init__(base_url=f"{API_BASE_URL}/axgate.House")

    # ------------------------------------------------------------------
    # Нормализация: street → Street
    # ------------------------------------------------------------------

    async def _request(self, method, action, **kwargs):
        result = await super()._request(method, action, **kwargs)
        for row in result:
            if "street" in row and "Street" not in row:
                row["Street"] = row.pop("street")
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
        logger.debug("HouseAPI.list response: %s", response)
        if not include_deleted:
            response = [row for row in response if not row.get("deleted")]
        return response

    async def create(self, street: int, number: str) -> Dict[str, Any]:
        payload = {"street": street, "number": number}
        return (await self._request("POST", "create", json=payload))[0]

    async def update(self, record_id: int, street: int, number: str) -> Dict[str, Any]:
        payload = {"id": record_id, "street": street, "number": number}
        return (await self._request("PUT", "update", json=payload))[0]
