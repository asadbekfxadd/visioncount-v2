# VisionCount v2 — Phase 1: Технический анализ и Implementation Plan

Основано на master-prompt архитектуре: локальный **Agent** на моноблоке филиала +
центральный **Cloud**. Цель Phase 1 — зафиксировать решения по разделу 84 master-prompt,
прежде чем писать код.

---

## 1. Что переиспользуем из текущего MVP (visioncount v1)

| Компонент v1 | Судьба в v2 |
|---|---|
| `backend/` (FastAPI + PostgreSQL) | Становится ядром **Cloud Backend**. Модели `Branch`, `Camera`, `AnalyticsEvent`, auth/JWT, WebSocket manager — переносим почти как есть. Нужно добавить: `Agent`, `AgentHeartbeat`, `Employee`, `Zone`, `Sale`, `SyncQueue`-совместимый ingest. |
| `frontend/` (Next.js) | Становится **Cloud Dashboard**. Экраны `/dashboard`, `/cameras`, `/branches`, `/analytics` переиспользуются, добавляем `/agents`, `/employees`, `/sales`, `/accuracy`. |
| `ai-service/` (detector.py, tracker.py, line_crossing.py, capture.py) | Логика переезжает **целиком**, но перестаёт быть докер-сервисом в облаке — становится ядром **VisionCount Agent** (Windows Service на моноблоке). RTSP больше не тянется через интернет. |
| `ai-service/demo_source.py` | Остаётся, но как режим Cloud (раздел 55 — Demo Mode отдельно от Production), не подмешивается в реальный pipeline. |

Ключевое архитектурное изменение: **Cloud перестаёт видеть камеры напрямую**. Все
RTSP/ONVIF-подключения — только с Agent, в локальной сети филиала. Это снимает
сегодняшнюю проблему с пробросом портов (`81.95.228.80:8098`) полностью — она была
следствием неправильной архитектуры (Cloud тянет видео через интернет), а не
недостатка конфигурации.

---

## 2. Технические риски

| Риск | Митигация |
|---|---|
| Моноблоки филиалов — неизвестная конфигурация (CPU/RAM/GPU) | Agent должен уметь работать на чистом CPU (как мы уже настроили torch CPU-only в v1); собрать инвентаризацию реальных моноблоков по 15 точкам перед Phase 3 |
| Windows Service + автозапуск + автообновление — незнакомая область (весь опыт команды — Linux/Docker) | Заложить время на Phase 3 отдельно, использовать готовые библиотеки (`pywin32`, NSSM, или `pyinstaller` + Task Scheduler как fallback вместо полноценного Windows Service) |
| SQLite → PostgreSQL sync с идемпотентностью | Использовать `event_id` (UUID, генерируется на Agent) как primary key на Cloud — INSERT ... ON CONFLICT DO NOTHING закрывает дубли без сложной логики |
| ONVIF discovery в реальных сетях филиалов (разные вендоры, VLAN) | Fallback на ручной ввод RTSP всегда доступен (как мы делали сегодня для Hikvision DS-2CD1343G0-I) — не блокировать MVP на ONVIF |
| Employee classification без face recognition — точность под вопросом | Начать с простого правила (zone + время нахождения + trajectory), собрать Accuracy Test (раздел 24) на реальной точке (Atlas Chimgan) прежде чем усложнять |
| 15 филиалов — 15 разных моноблоков, разный Windows/железо | Пилот на одном филиале (Atlas Chimgan, камера уже известна) до тиражирования |

---

## 3. Требования к моноблоку (минимальные, CPU-only)

- Windows 10/11, x64
- CPU: 4 ядра (YOLOv8n на CPU ~5-10 FPS на одну камеру при разумном resize)
- RAM: 4 GB свободных на Agent-процесс
- Диск: 2 GB под SQLite + логи + модель (с ротацией)
- Сеть: доступ к камере в локальной сети + исходящий HTTPS/WSS к Cloud (никаких входящих портов)

## 4. Требования к камерам

- RTSP-совместимость (подтверждено на Hikvision DS-2CD1343G0-I, sub-stream `/Streaming/Channels/102`)
- ONVIF — опционально, ускоряет discovery, не обязателен
- Рекомендация: sub-stream для детекции (ниже битрейт, эффективнее для CPU-инференса)

---

## 5. Database schema — Cloud (PostgreSQL)

Дополнительно к тому, что уже есть в v1 (`companies`, `branches`, `cameras`, `users`,
`analytics_events`):

```
agents
  id (uuid, pk)
  branch_id (fk)
  pairing_token_hash
  agent_version
  status (online/offline)
  last_heartbeat_at
  created_at

agent_heartbeats
  id, agent_id (fk), timestamp, cpu_usage, memory_usage, disk_space,
  camera_status (jsonb), ai_status, sync_status

employees
  id, branch_id (fk), name, role (enum), badge_id (nullable), status, created_at

zones
  id, camera_id (fk), zone_type (entry_line/exit_line/employee_zone), polygon (jsonb)

visitor_events   -- заменяет часть analytics_events, добавляет global_visitor_id
  id (uuid, from Agent), branch_id, camera_id, global_visitor_id,
  event_type (ENTRY/EXIT/EMPLOYEE_ENTRY/EMPLOYEE_EXIT),
  track_id, confidence, timestamp, synced_at

sales / sales_receipts
  id, branch_id, receipt_number, amount, timestamp,
  unique(branch_id, date, receipt_number)  -- защита от дублей импорта

hourly_statistics / daily_statistics
  branch_id, period_start, visitors, receipts, sales, conversion (materialized/cron)
```

Индексы: `(branch_id, timestamp)`, `(camera_id, timestamp)` на всех событийных таблицах.

## 6. Database schema — Agent (SQLite)

Зеркало Cloud-схемы в уменьшенном виде + `sync_queue`:

```
sync_queue
  event_id (uuid, pk), payload (json), created_at, synced_at (nullable),
  retry_count, next_retry_at
```

Sync engine: батчами по N событий, `POST /agent/sync` с `event_id` списком,
экспоненциальный backoff при ошибках сети.

---

## 7. API contract: Agent ↔ Cloud

```
POST /agents/pair            {pairing_code} -> {agent_id, agent_token}
POST /agent/heartbeat        (Bearer agent_token) {cpu, ram, disk, camera_status, ai_status}
POST /agent/events           (Bearer agent_token) [{event_id, camera_id, event_type, track_id, timestamp, ...}]
GET  /agent/config           (Bearer agent_token) -> {cameras: [...], zones: [...], employees: [...]}
POST /agent/sync             batched idempotent event upload
```

Auth: каждый Agent получает уникальный долгоживущий токен при pairing (не общий
`SERVICE_KEY`, как было в v1 — это была временная заглушка, в v2 так делать нельзя,
раз токен теперь живёт на физическом устройстве в филиале).

## 8. Security model

- Agent → Cloud: только исходящие HTTPS/WSS, TLS обязателен
- Agent token: уникальный per-agent, ревокируется через `/agents/{id}/revoke`
- Пароли камер: хранятся только на Agent (SQLite, зашифрованы локальным ключом, привязанным к машине — DPAPI на Windows), **не отправляются в Cloud**
- Pairing code: одноразовый, короткий TTL (аналогично today's Fernet-ключ фиксу — обязательно persisted key, не генерируемый заново при рестарте)

## 9. Cross-camera strategy (MVP-уровень)

Для Phase 5-6 достаточно: trajectory + временное окно + направление, **без**
визуальной re-identification (никакого биометрического профиля — раздел 50).
Полноценный cross-camera matching — можно отложить до филиалов с 2+ камерами;
Atlas Chimgan пилотируется с одной камерой, что упрощает Phase 1 тестирование.

## 10. Employee classification strategy (MVP-уровень)

Старт: **zone-based + dwell-time** правило (раздел 15-16) с порогом confidence.
Explicit "low confidence → не исключать" (раздел 19). Badge/BLE — Phase 11+, не MVP.

## 11. Accuracy strategy

Реализовать Accuracy Test (раздел 24) как первую фичу после базового pipeline —
именно то, что вчера обсуждали как "прогнать и сверить с ручным подсчётом". Это
даёт объективную метрику для демонстрации руководству, вместо "вроде работает".

---

## 12. Project structure

```
/visioncount
  /cloud
    /frontend        (Next.js — из v1 frontend/)
    /backend          (FastAPI — из v1 backend/)
  /agent
    /core             (main loop, config)
    /camera           (RTSP capture, ONVIF discovery — из v1 ai-service/capture.py)
    /ai                (detector.py, tracker.py — из v1 ai-service/)
    /tracking          (line_crossing.py — из v1)
    /employee          (classification engine — новое)
    /accuracy          (quality engine — новое)
    /sync              (sync queue, retry — новое)
    /database          (SQLite models — новое)
    /windows-service   (service wrapper, автозапуск — новое)
    /ui                (localhost:8765 — новое, минимальный HTML/JS)
  /shared
    /schemas           (общие Pydantic-модели для API contract)
  /tests
  /docs
    PHASE1-PLAN.md      (этот файл)
    master-prompt.md    (исходное ТЗ)
  /docker               (только для /cloud)
  README.md
```

---

## 13. Implementation plan (12 фаз, из раздела 82 master-prompt)

| Phase | Содержание | Готовность на старте |
|---|---|---|
| 1 | Architecture, repo, DB schema, API contract | ✅ этот документ |
| 2 | Cloud auth, companies, branches, agents, pairing | Частично — auth/branches уже есть в v1 backend |
| 3 | Windows Agent skeleton, Service, local UI, heartbeat | С нуля |
| 4 | Camera discovery, ONVIF, RTSP, diagnostics | Частично — `capture.py` из v1 переносим |
| 5 | Person detection, tracking, line crossing | Частично — `detector.py`, `tracker.py`, `line_crossing.py` из v1 переносим |
| 6 | Employee classification, zones, Accuracy Engine | С нуля |
| 7 | SQLite, offline mode, Sync Engine | С нуля |
| 8 | Cloud analytics, dashboard, realtime | Частично — dashboard/WebSocket уже есть в v1 |
| 9 | Sales import (Excel/CSV), conversion | С нуля (но есть опыт из Li-Ning ABC-анализа Excel-пайплайнов) |
| 10 | Reports, alerts, multi-branch analytics | Частично — alerts UI есть в v1 |
| 11 | Auto recovery, auto update, security hardening | С нуля |
| 12 | E2E testing, performance testing, production deploy | С нуля |

**Рекомендуемый порядок для пилота на Atlas Chimgan:** Phase 1 → 3 → 4 → 5 (доехать
до реального ENTRY/EXIT с одной камерой) → 2 → 8 (подключить к Cloud, увидеть на
дашборде) → 7 (offline/sync) → 6 (employee exclusion) → остальное по необходимости.
Это даёт рабочий видимый результат на реальной точке быстрее, чем строгий линейный
порядок 1→12.

---

## 14. Первая конкретная задача для Claude Code

1. Прочитать этот файл + `docs/master-prompt.md`
2. Создать структуру репозитория из раздела 12
3. Скопировать `backend/` и `frontend/` из v1 в `/cloud`, `ai-service/*.py` (detector,
   tracker, line_crossing, capture) в `/agent/ai` и `/agent/camera`
4. Начать Phase 3 (Windows Agent skeleton) с целью: Agent на Windows, читает
   `rtsp://81.95.228.80:8098/Streaming/Channels/102` (или локальный IP камеры,
   если Agent физически ставится в сети Atlas Chimgan — предпочтительно) и печатает
   FPS в консоль — простейший сквозной тест перед подключением AI pipeline.
