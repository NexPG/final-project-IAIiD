# Gate 5 report: деплой

**Этап:** 5. Деплой  
**Владелец:** Евгений Кононов  
**Статус:** закрыт

## Что сделано

- Multi-stage Dockerfile, non-root, healthcheck.
- Compose: api + Prometheus, `API_PORT`.
- Model/config read-only.
- Smoke 5/5 на uvicorn и в Docker.
- Rollback: предыдущий artifact + перезапуск.
- Production-маршрут описан.

## Проверки

```text
docker compose build       — ok
docker compose up -d --wait — api + prometheus healthy
python scripts/smoke.py    — 5/5
```

## Артефакты

- [`deployment.md`](deployment.md)
- `docker/Dockerfile`
- `docker/docker-compose.yml`
- `scripts/smoke.py`

## Gate 5

Docker build/up, smoke, healthcheck, rollback описаны и проверены.  
**Закрыт.**
