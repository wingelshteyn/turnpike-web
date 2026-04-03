"""API-клиент для типов территорий (axgate.RegionType).

Поля и CRUD-интерфейс совпадают с PartnerTypeAPI (Brief, Name).
"""

from ..config import API_BASE_URL
from .base import BaseAPI
from .brief_name_crud import BriefNameCRUDMixin


class RegionTypeAPI(BriefNameCRUDMixin, BaseAPI):
    def __init__(self):
        super().__init__(base_url=f"{API_BASE_URL}/axgate.RegionType")
