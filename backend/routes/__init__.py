"""Регистрация всех маршрутов приложения."""

from routes.auth import router as auth_router
from routes.cameras import router as cameras_router
from routes.partner_types import router as partner_types_router
from routes.region_types import router as region_types_router
from routes.partners import router as partners_router
from routes.regions import router as regions_router
from routes.cities import router as cities_router
from routes.streets import router as streets_router
from routes.houses import router as houses_router
from routes.contact_types import router as contact_types_router
from routes.clients import router as clients_router
from routes.contacts import router as contacts_router

__all__ = [
    "auth_router",
    "cameras_router",
    "partner_types_router",
    "region_types_router",
    "partners_router",
    "regions_router",
    "cities_router",
    "streets_router",
    "houses_router",
    "contact_types_router",
    "clients_router",
    "contacts_router",
]
