"""Кэшированные загрузки справочников (TTL) для снижения нагрузки на внешний API."""

from __future__ import annotations

from __future__ import annotations

from typing import Any

from .api import CityAPI, PartnerTypeAPI, RegionTypeAPI
from .cache_ttl import AsyncTTLCache

_ref_cache = AsyncTTLCache(ttl_seconds=300.0)


async def partner_types_list() -> list[dict[str, Any]]:
    async def _fetch() -> list[dict[str, Any]]:
        async with PartnerTypeAPI() as api:
            return await api.list()

    return await _ref_cache.get_or_fetch("PartnerTypeAPI.list", _fetch)


async def region_types_list() -> list[dict[str, Any]]:
    async def _fetch() -> list[dict[str, Any]]:
        async with RegionTypeAPI() as api:
            return await api.list()

    return await _ref_cache.get_or_fetch("RegionTypeAPI.list", _fetch)


async def cities_list(include_deleted: bool) -> list[dict[str, Any]]:
    key = f"CityAPI.list:{include_deleted}"

    async def _fetch() -> list[dict[str, Any]]:
        async with CityAPI() as api:
            return await api.list(include_deleted=include_deleted)

    return await _ref_cache.get_or_fetch(key, _fetch)


def invalidate_cities_cache() -> None:
    _ref_cache.invalidate_prefix("CityAPI.list")


def invalidate_partner_types_cache() -> None:
    _ref_cache.invalidate_prefix("PartnerTypeAPI.list")


def invalidate_region_types_cache() -> None:
    _ref_cache.invalidate_prefix("RegionTypeAPI.list")
