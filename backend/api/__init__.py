"""API-клиенты для работы с внешним API axioma24."""

from .base import BaseAPI
from .partner_type import PartnerTypeAPI
from .region_type import RegionTypeAPI
from .partner import PartnerAPI
from .region import RegionAPI
from .city import CityAPI
from .street import StreetAPI
from .house import HouseAPI
from .contact_type import ContactTypeAPI
from .client import ClientAPI
from .contact import ContactAPI

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
