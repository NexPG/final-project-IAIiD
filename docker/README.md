# Docker

Каталог для контейнеризации. Заполняется на этапе 5.

Планируемые файлы:

```text
docker/
├── Dockerfile
├── docker-compose.yml
└── prometheus/
    └── prometheus.yml
```

## Требования

- Multi-stage сборка.
- Базовый образ `python:3.12-slim`.
- Non-root пользователь.
- Healthcheck на `/health/ready`.
- Модель копируется в образ или монтируется read-only.
- Секреты передаются через `.env`, не через образ.
- `docker compose up` поднимает API, Prometheus и Grafana.

CI/CD на GitHub не используется: сборка и проверка выполняются локально.
