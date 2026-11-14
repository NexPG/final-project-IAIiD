# Деплой и запуск

**Статус:** реализовано (v1), этап 5  
**Источник требований:** [`TZ.md`](../01_task/TZ.md), §11; вебинары В10–В11

## 1. Учебный маршрут

CI/CD на GitHub не используется. Запуск и проверка — локально.

### venv

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
pip install -e ".[dev,ml]"
python scripts/build_dataset.py --config configs/data.yaml
python scripts/search_models.py --n-iter 12
uvicorn music_support_triage.api.app:app --reload
```

### Docker Compose

```bash
docker compose -f docker/docker-compose.yml up --build
```

Если порт 8000 занят, задайте `API_PORT`:

```powershell
$env:API_PORT="8010"; docker compose -f docker/docker-compose.yml up --build
```

| Сервис | Порт | Назначение |
|---|---|---|
| `api` | 8000 | FastAPI |
| `prometheus` | 9090 | Метрики и alert rules |

`db`/`grafana` не входят в учебный минимум. Feedback хранится в памяти процесса; в production — PostgreSQL. Артефакт модели монтируется read-only из `artifacts/`.

## 2. Dockerfile

- `python:3.12-slim`;
- copy requirements → install → copy code;
- non-root;
- model artifact read-only;
- `EXPOSE 8000`;
- `CMD uvicorn`;
- healthcheck;
- `.dockerignore`.

## 3. Smoke

```bash
python scripts/smoke.py --base-url http://127.0.0.1:8000
```

Проверяются `/healthcheck`, `/model-info`, `/v1/classify`, `/v1/classify/batch`, `/metrics`. Локально все проверки пройдены.

Ручной пример:

```bash
curl -X POST http://localhost:8000/v1/classify \
  -H "Content-Type: application/json" \
  -d "{\"text\":\"I was charged twice for my subscription\"}"
```

Ожидается `200`, `topic=payment`, `queue=billing`.

## 4. Стратегия деплоя

Выбрана **shadow → canary → rollback**:

| Этап | Действие | Критерий |
|---|---|---|
| Shadow | Новая модель на копии трафика | Метрики не хуже |
| Canary 5% | 5% трафика | 5xx < 1%, p95 < 500 мс |
| Canary 25/50% | Постепенно | Метрики стабильны |
| 100% | Полный перевод | Нет деградации |
| Rollback | Предыдущий образ/модель | Критерии нарушены |

Критерии успеха:

- 5xx < 1%;
- p95 ≤ 500 мс;
- selective precision не ниже текущей;
- override rate не хуже +5 п.п.;
- нет PII-инцидентов.

Rollback:

- решение: владелец этапа 5 + дежурный;
- ≤ 10 минут;
- уже обработанные запросы не переобрабатываем;
- feedback сохраняем;
- предыдущий образ и артефакт хранятся.

## 5. Production-маршрут (не разворачиваем)

- reverse proxy + TLS;
- 2+ реплики;
- model registry + canary;
- очередь;
- PostgreSQL;
- object storage;
- secrets manager;
- централизованные логи;
- blue-green/canary.

## 6. Чек-лист

- [x] Dockerfile собирается: `docker compose build` — успешно.
- [x] Compose поднимает api + Prometheus: `up -d --wait` — оба healthy.
- [x] healthcheck.
- [x] smoke — 5/5 (uvicorn и Docker).
- [x] модель read-only volume.
- [x] секреты не в образе.
- [x] rollback описан.
- [x] README-инструкция.
- [ ] Проверка на чистой машине без `.venv`.
- [ ] Load test 20 RPS.
