# Docker

Реализовано:

```text
docker/
├── Dockerfile
└── docker-compose.yml
```

## Требования

- Multi-stage сборка.
- Базовый образ `python:3.12-slim`.
- Non-root пользователь.
- Healthcheck на `/healthcheck`.
- Модель копируется в образ и монтируется read-only.
- Секреты не попадают в образ.
- `docker compose up` поднимает API, Prometheus и Grafana.

## Проверка

```bash
docker compose -f docker/docker-compose.yml up -d --wait
python scripts/service/smoke.py --base-url http://127.0.0.1:8000
docker compose -f docker/docker-compose.yml down
```

CI/CD на GitHub не используется: сборка и проверка выполняются локально.
