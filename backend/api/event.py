"""API-клиент для событий (axgate.Event).

Важно: `axgate.Event/list` — публичный эндпоинт, он не требует авторизации.
Поэтому здесь НЕ используем BaseAPI/TokenManager, чтобы не падать на auth.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import httpx
from fastapi import HTTPException

from ..config import API_BASE_URL


class EventAPI:
    """Клиент для работы с событиями (axgate.Event) без авторизации."""

    def __init__(self, base_url: str | None = None):
        self.base_url = (base_url or API_BASE_URL).rstrip("/")
        self.client: httpx.AsyncClient | None = None

    async def list_events(
        self,
        *,
        date1: str,
        date2: str,
        limit: int = 20,
        sample: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        params: Dict[str, Any] = {"date1": date1, "date2": date2, "limit": limit}
        if sample:
            params["sample"] = sample

        url = f"{self.base_url}/axgate.Event/list"
        try:
            resp = await self.client.get(url, params=params)
            resp.raise_for_status()
        except httpx.TimeoutException as exc:
            raise HTTPException(status_code=504, detail="Таймаут при загрузке событий.") from exc
        except httpx.ConnectError as exc:
            raise HTTPException(status_code=502, detail="Не удалось подключиться к API событий.") from exc
        except httpx.HTTPStatusError as exc:
            raise HTTPException(
                status_code=exc.response.status_code,
                detail=f"Ошибка API событий: {exc.response.text}",
            ) from exc

        payload = resp.json()
        if not payload.get("success", True):
            raise HTTPException(
                status_code=502,
                detail=f"API событий вернул ошибку: {payload.get('error') or payload.get('message')}",
            )

        return payload.get("result", {}).get("Table", [])

    async def __aenter__(self):
        self.client = httpx.AsyncClient(timeout=15)
        return self

    async def __aexit__(self, exc_type, exc, tb):
        if self.client:
            await self.client.aclose()
