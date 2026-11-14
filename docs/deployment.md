# Деплой и запуск

**Статус:** draft, заполняется на этапе 5  
**Источник требований:** [`TZ.md`](TZ.md), §11; вебинары В10–В11

## 1. Учебный маршрут

CI/CD на GitHub не используется. Запуск и проверка — локально.

### venv

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
pip install -e ".[dev]"
uvicorn music_support_triage.api.app:app --reload
```

### Docker Compose

```bash
docker compose -f docker/docker-compose.yml up --build
```

| Сервис | Порт | Назначение |
|---|---|---|
| `api` | 8000 | FastAPI |
| `db` | внутренний | feedback/logs |
| `prometheus` | 9090 | Метрики |
| `grafana` | 3000 | Дашборд |

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
curl -X POST http://localhost:8000/v1/classify \
  -H "Content-Type: application/json" \
  -d "{\"text\":\"Списали деньги за подписку, хотя я её отменил\"}"
```

Ожидается `200`, `topic=payment`, `queue=billing`.

Дополнительно:

```bash
curl http://localhost:8000/healthcheck
curl http://localhost:8000/model-info
curl http://localhost:8000/metrics
```

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

- [ ] Dockerfile собирается.
- [ ] Compose поднимает api+db.
- [ ] healthcheck.
- [ ] smoke.
- [ ] модель read-only.
- [ ] секреты не в образе.
- [ ] rollback описан.
- [ ] README-инструкция.
