"""API-клиенты для работы с внешним API axioma24."""

from api.base import BaseAPI
from api.partner_type import PartnerTypeAPI
from api.region_type import RegionTypeAPI
from api.partner import PartnerAPI
from api.region import RegionAPI
from api.city import CityAPI
from api.street import StreetAPI
from api.house import HouseAPI
from api.contact_type import ContactTypeAPI
from api.client import ClientAPI
from api.contact import ContactAPI

__all__ = [
    "BaseAPI",
    "PartnerTypeAPI",
    "RegionTypeAPI",
    "PartnerAPI",
    "RegionAPI",
    "CityAPI",
    "StreetAPI",
    "HouseAPI",
    "ContactTypeAPI",
    "ClientAPI",
    "ContactAPI",
]
