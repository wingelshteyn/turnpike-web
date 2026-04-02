"""Вспомогательные функции для маршрутов."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple, Type

from .api.base import BaseAPI

logger = logging.getLogger(__name__)


# ------------------------------------------------------------------
# Фильтрация записей (поиск)
# ------------------------------------------------------------------

# ------------------------------------------------------------------
# Пагинация
# ------------------------------------------------------------------

PER_PAGE = 20


def paginate(
    items: List[Dict[str, Any]],
    page: int = 1,
    per_page: int = PER_PAGE,
) -> tuple[List[Dict[str, Any]], int, int]:
    """Разбить список на страницы.

    Возвращает: (items_for_page, total_items, total_pages)
    """
    if page < 1:
        page = 1
    total = len(items)
    total_pages = max(1, (total + per_page - 1) // per_page)
    page = min(page, total_pages)
    start = (page - 1) * per_page
    return items[start : start + per_page], total, total_pages


# ------------------------------------------------------------------
# Фильтрация записей (поиск)
# ------------------------------------------------------------------

def filter_by_query(
    items: List[Dict[str, Any]],
    query: str,
    fields: List[str],
) -> List[Dict[str, Any]]:
    """Поиск по одному запросу в любом из указанных полей.

    Возвращает записи, у которых хотя бы одно поле содержит
    подстроку *query* (без учёта регистра).
    """
    query = (query or "").strip()
    if not query:
        return items

    q_lower = query.lower()
    result = []
    for item in items:
        for field in fields:
            value = item.get(field)
            if value is not None and q_lower in str(value).lower():
                result.append(item)
                break
    return result


# ------------------------------------------------------------------
# Разделение записей на активные / удалённые
# ------------------------------------------------------------------

async def fetch_split(
    api_class: Type[BaseAPI],
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Получить все записи и разделить на активные и удалённые."""
    async with api_class() as api:
        table = await api.list(include_deleted=True)

    active = [row for row in table if not row.get("deleted")]
    deleted = [row for row in table if row.get("deleted")]
    logger.debug(
        "%s: active=%d, deleted=%d", api_class.__name__, len(active), len(deleted),
    )
    return active, deleted


# ------------------------------------------------------------------
# Нормализация данных улиц для шаблонов
# ------------------------------------------------------------------

def normalize_streets_for_template(
    raw_streets: List[Dict[str, Any]],
    cities: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Приводит данные улиц к единому формату для шаблонов.

    * Маппит строковые имена городов на числовые ID.
    * Унифицирует регистр полей (``city`` → ``City``, ``Name`` → ``name``).
    """
    city_name_to_id: Dict[str, int] = {
        c["Name"].strip().lower(): c["id"] for c in cities
    }

    normalized: list[dict] = []
    for street in raw_streets:
        # --- City: строка → ID -----------------------------------------
        city_val = street.get("City") or street.get("city")
        if isinstance(city_val, str):
            city_id = city_name_to_id.get(city_val.strip().lower())
        else:
            city_id = city_val

        # --- name -------------------------------------------------------
        name = street.get("name") or street.get("Name")

        normalized.append({
            "id": street["id"],
            "name": name,
            "City": city_id,
            "created": street.get("created"),
            "updated": street.get("updated"),
            "deleted": street.get("deleted"),
        })

    return normalized
