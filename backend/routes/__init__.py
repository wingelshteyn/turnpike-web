"""Регистрация всех маршрутов приложения."""

from .auth import router as auth_router
from .cameras import router as cameras_router
from .partner_types import router as partner_types_router
from .region_types import router as region_types_router
from .partners import router as partners_router
from .regions import router as regions_router
from .cities import router as cities_router
from .streets import router as streets_router
from .houses import router as houses_router
from .contact_types import router as contact_types_router
from .clients import router as clients_router
from .contacts import router as contacts_router
from .analytics_pages import router as analytics_pages_router

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
    "analytics_pages_router",
]
