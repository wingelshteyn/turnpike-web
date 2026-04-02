## Turnpike Web

### Запуск (локально)

Установка зависимостей:

```bash
python -m pip install -r backend/requirements.txt
```

Запуск:

```bash
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8001
```

Откройте `http://127.0.0.1:8001/auth` и войдите `admin / admin`.

**Важно для сервера:** команду `uvicorn` нужно запускать **из корня репозитория** (рядом с папкой `backend/`), а не из `backend/`. Иначе пакет `backend` не найдётся, а `python main.py` из каталога `backend/` сломается на относительных импортах. В systemd/docker задайте `WorkingDirectory` / `WORKDIR` на корень проекта.

В проде без `--reload`:

```bash
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8001
```

За HTTPS включите `COOKIE_SECURE=true` (см. ниже).

### Переменные окружения

- **API_BASE_URL**: базовый URL внешнего API (по умолчанию `https://apiarm.axioma24.ru`)
- **HOST_AUTH**: URL сервиса авторизации (по умолчанию `https://apiarm.axioma24.ru/auth`)
- **COOKIE_SECURE**: `true/false` — ставить флаг `Secure` для cookie (в проде на HTTPS включить)
- **COOKIE_SAMESITE**: `lax/strict/none` — политика SameSite для cookie
- **TOKEN_CACHE_TTL_SECONDS**: TTL кэша токенов внешнего API (по умолчанию `600`)

