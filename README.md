# VisionCount — People Analytics SaaS

_"Understand every visitor."_

SaaS для видеоаналитики и подсчёта посетителей по IP-камерам: подключение камер по RTSP/ONVIF,
AI-подсчёт входов/выходов (YOLO + tracking + line crossing), realtime-дашборд по WebSocket,
мультитенантность, RBAC, отчёты.

## Архитектура

```
/frontend    Next.js 14 + TypeScript + Tailwind + shadcn-style UI + Recharts
/backend     FastAPI (async) + PostgreSQL (SQLAlchemy 2.0) + Redis + WebSocket
/ai-service  Python: RTSP → YOLO → tracker → line crossing → события (или Demo Mode)
/docker      docker-compose поднимает все сервисы одной командой
```

Поток данных:

```
RTSP-камера ──▶ ai-service (YOLO + tracker + line crossing)
                     │  POST /internal/events (X-Service-Key)
                     ▼
                 backend (FastAPI) ──▶ PostgreSQL (analytics_events)
                     │  broadcast
                     ▼
              WebSocket /ws/dashboard ──▶ frontend (live KPI, live-камера)
```

В **Demo Mode** (`DEMO_MODE=true`, включён по умолчанию) `ai-service` не открывает
реальный RTSP-поток, а генерирует правдоподобный поток ENTRY/EXIT-событий той же
формы, что и настоящий pipeline — поэтому backend, WebSocket и дашборд не отличают
демо-камеру от настоящей. Чтобы подключить реальную камеру, поставьте `DEMO_MODE=false`
и укажите её `rtsp_url` — заработает код в `ai-service/app/main.py:run_real_pipeline`.

## Быстрый старт

```bash
cp .env.example .env
# при необходимости отредактируйте пароли/секреты в .env
docker compose up --build
```

- Frontend: http://localhost:3000 (демо-логин: `owner@visioncount.uz` / `demo1234`)
- Backend API: http://localhost:8000 (Swagger — http://localhost:8000/docs)
- AI-service: работает в фоне, публикует события в backend и Redis

При первом старте backend сам создаёт таблицы (`Base.metadata.create_all`) и
засевает демо-компанию «VisionCount Retail» с 4 филиалами, камерами и пользователем-владельцем
(см. `backend/app/services/seed.py`).

## REST API (backend)

| Метод | Путь | Описание |
|---|---|---|
| POST | `/auth/login` | JWT-логин |
| GET | `/dashboard` | KPI дашборда (входы/выходы/внутри/конверсия) |
| GET | `/companies` | Компания текущего пользователя |
| GET/POST | `/branches` | Филиалы |
| GET/POST/PUT/DELETE | `/cameras`, `/cameras/{id}` | Камеры |
| POST | `/cameras/{id}/test` | Проверка соединения с камерой |
| PUT | `/cameras/{id}/config` | Настройка Line Crossing (координаты линий 0..1) |
| GET | `/analytics`, `/analytics/hourly`, `/analytics/daily`, `/analytics/heatmap` | Аналитика |
| GET/POST | `/reports` | Отчёты (CSV/Excel/PDF — экспорт-заглушка для MVP) |
| GET | `/alerts` | Уведомления |
| GET/POST | `/users` | Пользователи (RBAC) |
| WS | `/ws/dashboard` | Живой поток всех событий компании |
| WS | `/ws/cameras/{id}` | Живой поток событий одной камеры |
| POST | `/internal/events` | **Служебный**: сюда ai-service шлёт ENTRY/EXIT (требует `X-Service-Key`) |

## Роли (RBAC)

`OWNER` > `ADMIN` > `MANAGER` > `ANALYST` > `VIEWER` — иерархия проверяется в
`backend/app/deps.py::require_role`. Пароли камер шифруются (Fernet) и никогда не
возвращаются в API-ответах.

## Что уже реально работает

- Полная схема PostgreSQL (companies → branches → cameras → camera_configs → analytics_events, daily/hourly_statistics, alerts, reports, users) с нормализацией и `created_at/updated_at`.
- JWT-аутентификация, bcrypt-хеширование паролей, RBAC на каждом мутирующем эндпоинте.
- Мультитенантность: все выборки фильтруются по `company_id` текущего пользователя.
- Реальный WebSocket-broadcast (fan-out по каналам `dashboard` и `camera:{id}`).
- AI-сервис с абстрактным интерфейсом `detect() → track() → line_crossing()`, готовым
  принять реальную YOLO-модель (`ultralytics`) и RTSP-поток (`opencv` + FFmpeg) —
  сейчас включён `Demo Mode`, но код реального пайплайна не заглушка, а рабочая ветка.
- Frontend полностью на реальных fetch-запросах к backend + живой WebSocket на дашборде,
  без хардкода моковых данных (кроме initial skeleton loading).

## Что оставлено как явная точка расширения для продакшена

- **Алгоритм ByteTrack**: сейчас `tracker.py` использует лёгкий centroid/IOU-трекер
  без внешних зависимостей (интерфейс идентичен — легко заменить на пакет `bytetrack`).
- **Рендер CSV/Excel/PDF**: `POST /reports` создаёт запись и возвращает её; сама генерация
  файла и `file_url` — TODO для фонового воркера (Celery/RQ).
- **Alembic-миграции**: таблицы создаются через `Base.metadata.create_all` при старте
  (быстро для MVP/демо); для прод-раскатки стоит завести полноценные ревизии Alembic.
- **ONVIF discovery / PTZ**: зависимость `onvif-zeep` подключена, но автообнаружение камер
  в сети не реализовано — камеры добавляются вручную по IP/RTSP URL.

## Переменные окружения

См. `.env.example`. Ключевые:

- `DATABASE_URL` — `postgresql+asyncpg://...` (backend асинхронный)
- `SECRET_KEY` — используется и для подписи JWT, и как `X-Service-Key` между
  `ai-service` и `backend` (в проде — разделить на два разных секрета)
- `DEMO_MODE` — `true`/`false`
- `CAMERA_CREDENTIALS_ENCRYPTION_KEY` — ключ Fernet для шифрования паролей камер

## Локальная разработка без Docker

```bash
# backend
cd backend && python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# frontend
cd frontend && npm install && npm run dev

# ai-service
cd ai-service && pip install -r requirements.txt && python -m app.main
```

Нужны локально запущенные PostgreSQL и Redis (или оставьте их в docker-compose и
поднимайте только эти два сервиса: `docker compose up postgres redis`).

## Безопасность (аудит)
- WebSocket (`/ws/dashboard`, `/ws/cameras/{id}`) требуют JWT (`?token=`) и отдают события только своей компании.
- В production (`APP_ENV=production` или Railway) сервис не стартует с `SECRET_KEY`/`FERNET_KEY` по умолчанию, а демо-пользователь `owner@visioncount.uz / demo1234` не создаётся (если не задан `DEMO_MODE=true`).
- Ключ ai-service можно отделить от JWT-ключа: `SERVICE_KEY` (на обеих сторонах).
- Вход: не более 10 неудачных попыток за 15 минут на email и на адрес; роль нового пользователя не может быть выше роли создающего.
- Тесты: `cd backend && pip install pytest pytest-asyncio httpx aiosqlite && TEST_DATABASE_URL=postgresql+asyncpg://user:pass@host/db pytest tests`. Копия `cloud/` синхронизирована с `backend/` и `frontend/`.
