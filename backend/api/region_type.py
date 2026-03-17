"""API-клиент для типов территорий (axgate.RegionType).

Поля и CRUD-интерфейс совпадают с PartnerTypeAPI (Brief, Name).
"""

from config import API_BASE_URL
from api.partner_type import PartnerTypeAPI


class RegionTypeAPI(PartnerTypeAPI):
    def __init__(self):
        # Вызываем BaseAPI.__init__ напрямую, минуя PartnerTypeAPI
        super(PartnerTypeAPI, self).__init__(
            base_url=f"{API_BASE_URL}/axgate.RegionType",
        )
