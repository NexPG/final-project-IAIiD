# Этапы проекта и gates

**Правило:** этапы идут строго по порядку. Следующий этап не считается закрытым, пока не выполнен gate предыдущего. Артефакт каждого этапа — вход для следующего.

## Сводка

| Этап | Статус | Gate | Ключевой артефакт |
|---|---|---|---|
| 1. Задача | закрыт | задача, таксономия, метрики, данные | `TZ.md`, `README.md`, `data.md` |
| 2. Архитектура | закрыт | схема, API-контракт, OpenAPI, SLA, ADR | `architecture.md`, `api.md`, `openapi.json` |
| 3. Эксперименты | закрыт | 80/20, CV, HalvingRandomSearchCV, test один раз, CI, MLflow | `experiments.md`, `search_results.json`, `model_card.md` |
| 4. Тестирование | закрыт | data/model/API/contract tests, найденная проблема | `tests/`, `testing.md` |
| 5. Деплой | закрыт | Docker build/up, smoke, rollback | `Dockerfile`, `docker-compose.yml`, `deployment.md` |
| 6. Мониторинг | закрыт | метрики, ≥1 алерт, drift, runbook | `monitoring/`, `monitoring.md` |

## Этап 1. Задача

**Вход:** задание курса, проектная презентация, 16 вебинаров.

**Сделано:**

- тема: классификация обращений музыкального стриминга;
- 7 классов и очереди;
- метрики: macro-F1 + CI, selective precision, coverage;
- границы: учебный прототип, manual review;
- данные: TWCS + Bitext, объединённый пул, 80/20, CV вместо validation;
- роли 5 участников.

**Gate 1:** задача, вход/выход, метрики, ограничения и роли согласованы.  
**Артефакты:** [`TZ.md`](TZ.md), [`README.md`](../../README.md), [`data.md`](data.md), [`gate_report.md`](gate_report.md).

## Этап 2. Архитектура

**Вход:** Gate 1.

**Сделано:**

- модульный монолит FastAPI, online, embedded model;
- сравнение монолит/микросервисы, batch/stream, MaaS/embedded, classical ML/LLM;
- 3 узких места;
- API-контракт: classify, batch, feedback, healthcheck, model-info, metrics;
- единый формат ошибок и `X-Request-ID`;
- SLA и версионирование API/модели/данных;
- ADR-01…ADR-11;
- OpenAPI в `docs/02_architecture/openapi.json`;
- contract-тесты API и OpenAPI;
- схема `docs/02_architecture/architecture.png`.

**Gate 2:** схема читаема, контракт совпадает с кодом, OpenAPI валиден, ошибки и SLA описаны.  
**Артефакты:** [`architecture.md`](../02_architecture/architecture.md), [`api.md`](../02_architecture/api.md), [`openapi.json`](../02_architecture/openapi.json), [`gate_report.md`](../02_architecture/gate_report.md), `src/music_support_triage/api/`.

## Этап 3. Эксперименты

**Вход:** Gate 2 + данные.

**Сделано:**

- объединённый пул 13 427 строк: TWCS + Bitext;
- 80/20 со стратификацией одновременно по `(source, label)`: 10 713 train, 2 714 test;
- 5-fold `StratifiedGroupKFold` на train, стратификация по `(source, label)`;
- `HalvingRandomSearchCV`: 120 кандидатов, factor=2, resources 2000→4000→8000;
- выбор по mean CV macro-F1, test не используется;
- OOF-порог 0.85/0.05;
- одно измерение на test: macro-F1 0.855, 95% CI [0.791; 0.908];
- MLflow runs, model card.

**Gate 3:** split стратифицирован, CV и search воспроизводимы, test не использован для выбора, CI опубликован, MLflow заполнен.  
**Артефакты:** [`experiments.md`](../03_experiments/experiments.md), [`model_card.md`](../03_experiments/model_card.md), [`gate_report.md`](../03_experiments/gate_report.md), `artifacts/search_results.json`, MLflow.

## Этап 4. Тестирование

**Вход:** Gate 3.

**Сделано:**

- data validation: pandas + 8/8 Great Expectations;
- unit: очистка, PII, маппинг, split, dedup, routing;
- model: overall, per-class, robustness, edge, behavior, adversarial, subgroup;
- API: contract, batch, feedback, 422/503, OpenAPI, error envelope;
- 37 тестов, `ruff`, `mypy`, smoke;
- load test: 20 RPS, 30 s, 600 requests, 0 errors, p95 9.74 ms;
- найдены: отрицание, `content`/`recommendations`, mixed-source test.

**Gate 4:** критические сценарии покрыты, найденная проблема описана, quality gate зелёный.  
**Артефакты:** [`testing.md`](../04_testing/testing.md), [`gate_report.md`](../04_testing/gate_report.md), `tests/`, `data/processed/ge_report.json`.

## Этап 5. Деплой

**Вход:** Gate 4.

**Сделано:**

- multi-stage Dockerfile, non-root, healthcheck;
- Compose api + Prometheus, `API_PORT`;
- model/config read-only;
- smoke 5/5 на uvicorn и Docker;
- Docker load test: 20 RPS / 20 s, 400 requests, 0 errors, p95 52.72 ms;
- final model `search-logreg_word-20261114200534` внутри образа;
- rollback и production-маршрут описаны.

**Gate 5:** `docker compose build/up`, smoke, healthcheck, rollback.  
**Артефакты:** [`deployment.md`](../05_deployment/deployment.md), [`gate_report.md`](../05_deployment/gate_report.md), `docker/`.

## Этап 6. Мониторинг

**Вход:** Gate 5.

**Сделано:**

- `/metrics`, Prometheus;
- Grafana dashboard: инфраструктура, продукт, модель;
- 7 алертов: API down, model not ready, 5xx, latency, manual rate, other share, confidence;
- алерт `TriageApiDown` проверен в firing;
- drift-отчёт: PSI 0.003, KS 0.020, `other_share` 44.1% vs 44.5%;
- runbook и стратегия переобучения.

**Gate 6:** 3 уровня метрик, ≥1 алерт, drift-отчёт, runbook.  
**Артефакты:** [`monitoring.md`](../06_monitoring/monitoring.md), [`gate_report.md`](../06_monitoring/gate_report.md), `monitoring/`, `scripts/drift_report.py`.

## Что нельзя делать раньше

1. Нельзя менять API после Gate 2 без новой версии/ADR.
2. Нельзя выбирать модель по test.
3. Нельзя деплоить модель, не прошедшую Gate 4.
4. Нельзя включать auto-routing без selective precision ≥ 0.95 на test.
5. Нельзя менять split после Gate 3 без пересчёта всех метрик.
