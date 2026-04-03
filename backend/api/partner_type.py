"""API-клиент для типов партнёров (axgate.PartnerType)."""

from __future__ import annotations

from ..config import API_BASE_URL
from .base import BaseAPI
from .brief_name_crud import BriefNameCRUDMixin


class PartnerTypeAPI(BriefNameCRUDMixin, BaseAPI):
    def __init__(self):
        super().__init__(base_url=f"{API_BASE_URL}/axgate.PartnerType")
