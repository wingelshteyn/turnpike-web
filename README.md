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

**Проверка живости:** `GET /health` возвращает `{"status":"ok"}` и не требует авторизации (удобно для балансировщиков и мониторинга).

### Тесты

После `pip install -r backend/requirements.txt` из корня репозитория:

```bash
python -m pytest tests/
```

### Docker (сервер)

Нужны установленные **Docker** и **Docker Compose** (plugin `docker compose` или отдельный бинарник `docker-compose`).

1. Склонируйте репозиторий на сервер и перейдите в каталог проекта (рядом с `Dockerfile` и `docker-compose.yml`).

2. Сборка и запуск в фоне:

```bash
docker compose up -d --build
```

3. Приложение слушает **порт 8001** на хосте (`http://СЕРВЕР:8001`). Проверка: `curl -s http://127.0.0.1:8001/health` → `{"status":"ok"}`.

4. **Данные** (`users.json`, `sessions.json`) хранятся в именованном томе `turnpike_data`, смонтированном в контейнере как `/data` (переменная `TURNPIKE_DATA_DIR`). При пересоздании контейнера пользователи и сессии сохраняются.

5. За HTTPS-прокси (nginx, Caddy, Traefik) раскомментируйте в `docker-compose.yml` переменную `COOKIE_SECURE: "true"` (или передайте через `environment`), иначе cookie с флагом Secure могут не устанавливаться в браузере.

6. Другой порт на хосте, например **8080**:

```yaml
# в docker-compose.yml в секции ports:
ports:
  - "8080:8001"
```

7. Остановка и удаление контейнера (том с данными **не** удаляется):

```bash
docker compose down
```

8. Запуск без Compose (вручную):

```bash
docker build -t turnpike-web .
docker run -d --name turnpike-web -p 8001:8001 \
  -e TURNPIKE_DATA_DIR=/data \
  -v turnpike_data:/data \
  --restart unless-stopped \
  turnpike-web
```

Переменная **PORT** внутри контейнера задаёт порт процесса uvicorn (по умолчанию `8001`); при смене порта в `docker run` добавьте `-e PORT=...` и согласуйте с `-p` и пробросом в nginx.

### Переменные окружения

- **API_BASE_URL**: базовый URL внешнего API (по умолчанию `https://apiarm.axioma24.ru`)
- **HOST_AUTH**: URL сервиса авторизации (по умолчанию `https://apiarm.axioma24.ru/auth`)
- **COOKIE_SECURE**: `true/false` — ставить флаг `Secure` для cookie (в проде на HTTPS включить)
- **COOKIE_SAMESITE**: `lax/strict/none` — политика SameSite для cookie
- **TOKEN_CACHE_TTL_SECONDS**: TTL кэша токенов внешнего API (по умолчанию `600`)
- **TURNPIKE_DATA_DIR**: каталог для `users.json` и `sessions.json` (по умолчанию каталог пакета `backend`; в Docker образе задаётся `/data`)
- **PORT**: порт uvicorn (по умолчанию `8001`; в `Dockerfile` используется в команде запуска)

