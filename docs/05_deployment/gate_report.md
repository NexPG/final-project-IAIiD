# Gate 5 report: деплой

**Этап:** 5. Деплой  
**Владелец:** Евгений Кононов  
**Статус:** закрыт

## Что сделано

- Multi-stage Dockerfile, non-root, healthcheck.
- Compose: api + Prometheus + Grafana, `API_PORT`.
- Feedback хранится в SQLite-volume и переживает перезапуск API.
- Model/config read-only.
- Smoke 5/5 на uvicorn и в Docker.
- Rollback: предыдущий artifact + перезапуск.
- Production-маршрут описан.

## Проверки

```text
docker compose build        — ok
docker compose up -d --wait — api + prometheus healthy
python scripts/service/smoke.py     — 5/5
load test 20 RPS / 20 s     — 400 requests, 0 errors, p95 52.72 ms
model-info                  — search-logreg_word-20261114200534
image size                  — 708 MB
```

## Артефакты

- [`deployment.md`](deployment.md)
- `docker/Dockerfile`
- `docker/docker-compose.yml`
- `scripts/service/smoke.py`

## Gate 5

Docker build/up, smoke, healthcheck, rollback описаны и проверены.  
**Закрыт.**
