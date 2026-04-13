"""Демо-строки журнала «События» для шаблона и фильтров (тестовый набор)."""

from __future__ import annotations

# Кортеж подписей важности по индексу sev (0..2)
SEV_LABELS: tuple[str, ...] = ("Норма", "Внимание", "Высокая")

STATUS_TO_MOD: dict[str, str] = {
    "Новое": "new",
    "Обработано": "done",
    "Закрыто": "closed",
}

# Тестовые события: хронология сверху вниз — от новых к старым
EVENTS_DEMO_ROWS: list[dict[str, str | int]] = [
    {
        "event": "Критическая ошибка: недоступен шлюз API",
        "detail": "HTTP 503 · повтор через 30 с · tp…k901",
        "device": "API Аксиома24",
        "dt": "10.04.2026 10:18",
        "sev": 2,
        "status": "Новое",
    },
    {
        "event": "Создание записи в справочнике",
        "detail": "Партнёры · Москва · tp…a172",
        "device": "Веб-приложение",
        "dt": "10.04.2026 09:47",
        "sev": 0,
        "status": "Обработано",
    },
    {
        "event": "Попытка входа с неверным паролем",
        "detail": "IP 192.168.1.42 · 3 попытки · tp…u204",
        "device": "Авторизация",
        "dt": "10.04.2026 09:12",
        "sev": 1,
        "status": "Новое",
    },
    {
        "event": "Ошибка ответа API",
        "detail": "Токен / таймаут · tp…x455",
        "device": "API Аксиома24",
        "dt": "10.04.2026 08:12",
        "sev": 2,
        "status": "Обработано",
    },
    {
        "event": "Открыт поток камеры",
        "detail": "Античный скальд · MJPEG · tp…0324",
        "device": "Камеры",
        "dt": "10.04.2026 07:58",
        "sev": 0,
        "status": "Обработано",
    },
    {
        "event": "Вход в систему",
        "detail": "Сессия cookie · tp…d3a1",
        "device": "Авторизация",
        "dt": "10.04.2026 07:22",
        "sev": 0,
        "status": "Обработано",
    },
    {
        "event": "Импорт: 12 строк с ошибкой валидации",
        "detail": "Файл partners_q1.csv · строки 4,7,11 · tp…v833",
        "device": "Импорт CSV",
        "dt": "09.04.2026 19:05",
        "sev": 1,
        "status": "Новое",
    },
    {
        "event": "Массовое обновление контактов",
        "detail": "Контакты · tp…f112",
        "device": "Импорт CSV",
        "dt": "09.04.2026 18:33",
        "sev": 0,
        "status": "Обработано",
    },
    {
        "event": "Потеря кадра превью",
        "detail": "HTTP превью · Античный скальд · tp…c701",
        "device": "Камеры",
        "dt": "09.04.2026 14:03",
        "sev": 1,
        "status": "Закрыто",
    },
    {
        "event": "Редактирование региона",
        "detail": "Регионы · tp…386b",
        "device": "Веб-приложение",
        "dt": "09.04.2026 11:47",
        "sev": 0,
        "status": "Обработано",
    },
    {
        "event": "Отказ CSRF",
        "detail": "Форма без токена · tp…fa21",
        "device": "Веб-приложение",
        "dt": "09.04.2026 10:15",
        "sev": 1,
        "status": "Новое",
    },
    {
        "event": "Экспорт справочника",
        "detail": "Типы партнёров · tp…т789",
        "device": "Веб-приложение",
        "dt": "09.04.2026 09:05",
        "sev": 0,
        "status": "Обработано",
    },
    {
        "event": "Синхронизация расписания: сбой DNS",
        "detail": "apiarm.axioma24.ru · NXDOMAIN · tp…dns1",
        "device": "API Аксиома24",
        "dt": "08.04.2026 17:40",
        "sev": 2,
        "status": "Закрыто",
    },
    {
        "event": "Долгий запрос к API",
        "detail": "> 5 с · tp…м789",
        "device": "API Аксиома24",
        "dt": "08.04.2026 16:30",
        "sev": 1,
        "status": "Закрыто",
    },
    {
        "event": "Выход из системы (явный)",
        "detail": "Сессия завершена · tp…out9",
        "device": "Авторизация",
        "dt": "08.04.2026 12:00",
        "sev": 0,
        "status": "Обработано",
    },
    {
        "event": "Тестовое событие: проверка журнала",
        "detail": "Служебная запись для UI · tp…test",
        "device": "Веб-приложение",
        "dt": "07.04.2026 08:00",
        "sev": 0,
        "status": "Закрыто",
    },
]

# Если основной список пуст (ошибка деплоя), журнал всё равно покажет одну строку
_MIN_FALLBACK: list[dict[str, str | int]] = [
    {
        "event": "Демо-событие",
        "detail": "Запись по умолчанию · обновите backend/demo_events.py",
        "device": "Веб-приложение",
        "dt": "01.01.2026 00:00",
        "sev": 0,
        "status": "Обработано",
    },
]


def _enrich_row(r: dict[str, str | int]) -> dict[str, str | int]:
    row = dict(r)
    sev = int(row["sev"])
    row["sev_label"] = SEV_LABELS[sev]
    row["st_mod"] = STATUS_TO_MOD[str(row["status"])]
    blob = f"{row['event']} {row['detail']} {row['device']} {row['dt']}"
    row["search_blob"] = blob.lower()
    return row


def prepared_events_rows() -> list[dict[str, str | int]]:
    """Добавляет sev_label, st_mod, search_blob для шаблона."""
    source = EVENTS_DEMO_ROWS if EVENTS_DEMO_ROWS else _MIN_FALLBACK
    return [_enrich_row(r) for r in source]


def journal_rows_for_page() -> list[dict[str, str | int]]:
    """Страница «События»: всегда непустой список тестовых строк."""
    rows = prepared_events_rows()
    if rows:
        return rows
    return [_enrich_row(r) for r in _MIN_FALLBACK]
