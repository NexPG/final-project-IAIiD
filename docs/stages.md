# Этапы проекта и gates

**Правило:** этапы идут строго по порядку. Следующий этап не считается закрытым, пока не выполнен gate предыдущего. Артефакт каждого этапа — вход для следующего.

## Сводка

| Этап | Статус | Gate | Ключевой артефакт |
|---|---|---|---|
| 1. Задача | закрыт | задача, таксономия, метрики, данные | `TZ.md`, `README.md`, `data.md` |
| 2. Архитектура | закрыт | схема, API-контракт, OpenAPI, SLA, ADR | `architecture.md`, `api.md`, `openapi.json` |
| 3. Эксперименты | в работе | CV, RandomizedSearchCV, test один раз, CI, MLflow | `experiments.md`, `search_results.json`, `model_card.md` |
| 4. Тестирование | базово закрыт | data/model/API/contract tests, найденная проблема | `tests/`, `testing.md` |
| 5. Деплой | базово закрыт | Docker build/up, smoke, rollback | `Dockerfile`, `docker-compose.yml`, `deployment.md` |
| 6. Мониторинг | базово закрыт | метрики, ≥1 алерт, drift, runbook | `monitoring/`, `monitoring.md` |

«Базово закрыт» = механика работает, но финальная приёмка ждёт human-verified test.

## Этап 1. Задача

**Вход:** задание курса, проектная презентация, 16 вебинаров.

**Сделано:**

- тема: классификация обращений музыкального стриминга;
- 7 классов и очереди;
- метрики: macro-F1 + CI, selective precision, coverage;
- границы: учебный прототип, manual review;
- план данных: TWCS + Bitext + synthetic, train/test, CV вместо validation;
- роли 5 участников.

**Gate 1:** задача, вход/выход, метрики, ограничения и роли согласованы.  
**Статус:** закрыт.  
**Артефакты:** [`TZ.md`](TZ.md), [`README.md`](../README.md), [`data.md`](data.md).

## Этап 2. Архитектура

**Вход:** Gate 1.

**Сделано:**

- модульный монолит FastAPI, online, embedded model;
- сравнение монолит/микросервисы, batch/stream, MaaS/embedded, classical ML/LLM;
- 3 узких места;
- API-контракт: `/v1/classify`, batch, feedback, healthcheck, model-info, metrics;
- единый формат ошибок и `X-Request-ID`;
- SLA и версионирование API/модели/данных;
- ADR-01…ADR-11;
- OpenAPI выгружен в `docs/openapi.json`;
- contract-тесты API и OpenAPI.

**Gate 2:** схема читаема, контракт совпадает с кодом, OpenAPI валиден, ошибки и SLA описаны.  
**Статус:** закрыт.  
**Артефакты:** [`architecture.md`](architecture.md), [`api.md`](api.md), [`openapi.json`](openapi.json), `src/music_support_triage/api/`.

## Этап 3. Эксперименты

**Вход:** Gate 2 + данные.

**Сделано:**

- train 11 325, test 439;
- 5-fold `StratifiedGroupKFold` по `conversation_id`;
- `RandomizedSearchCV(n_iter=12)` по 4 семействам;
- выбор по mean CV macro-F1, test не используется;
- OOF-порог 0.85/0.05;
- одно измерение на test: macro-F1 0.657, 95% CI [0.564; 0.739];
- bootstrap CI, balanced test, drift-отчёт;
- MLflow runs, model card.

**Gate 3:** CV и search воспроизводимы, test не использован для выбора, CI опубликован, MLflow заполнен.  
**Статус:** **в работе** — механика выполнена, но test weak. Финальный gate требует human-verified test и повторного замера.  
**Артефакты:** [`experiments.md`](experiments.md), [`model_card.md`](model_card.md), `artifacts/search_results.json`, MLflow.

## Этап 4. Тестирование

**Вход:** Gate 3 (модель и контракт).

**Сделано:**

- data validation: pandas + 8/8 Great Expectations;
- unit: очистка, PII, маппинг, split, dedup, routing;
- model: overall, per-class, robustness, edge, behavior, adversarial, subgroup;
- API: contract, batch, feedback, 422/503, OpenAPI, error envelope;
- 37 тестов, `ruff`, `mypy`, smoke;
- найдены: отрицание, `content`/`recommendations`, distribution shift.

**Gate 4:** критические сценарии покрыты, найденная проблема описана, quality gate зелёный.  
**Статус:** базово закрыт; после human test добавить load/contract на финальных данных.  
**Артефакты:** [`testing.md`](testing.md), `tests/`, `data/processed/ge_report.json`.

## Этап 5. Деплой

**Вход:** Gate 4.

**Сделано:**

- multi-stage Dockerfile, non-root, healthcheck;
- Compose api + Prometheus, `API_PORT`;
- model/config read-only;
- smoke 5/5 на uvicorn и Docker;
- rollback и production-маршрут описаны.

**Gate 5:** `docker compose build/up`, smoke, healthcheck, rollback.  
**Статус:** базово закрыт; осталось проверить на чистой машине и load test.  
**Артефакты:** [`deployment.md`](deployment.md), `docker/`.

## Этап 6. Мониторинг

**Вход:** Gate 5.

**Сделано:**

- `/metrics`, Prometheus;
- 4 алерта: API down, model not ready, 5xx, latency;
- алерт `TriageApiDown` проверен в firing;
- drift-отчёт: PSI 0.868, KS 0.377, `other_share` 34.8% vs 74.5%;
- runbook и стратегия переобучения.

**Gate 6:** 3 уровня метрик, ≥1 алерт, drift-отчёт, runbook.  
**Статус:** базово закрыт; production drift требует реальных логов.  
**Артефакты:** [`monitoring.md`](monitoring.md), `monitoring/`, `scripts/drift_report.py`.

## Текущая точка

- Gate 1 — закрыт.
- Gate 2 — закрыт (контракт + OpenAPI + ошибки + SLA).
- Gate 3 — в работе: осталось human-verified test 400 и повторный замер.
- Gates 4–6 — базово закрыты, финальная приёмка после Gate 3.

## Что нельзя делать раньше

1. Нельзя считать Stage 3 закрытым до human-verified test.
2. Нельзя менять API после Gate 2 без новой версии/ADR.
3. Нельзя выбирать модель по test.
4. Нельзя деплоить модель, не прошедшую Gate 4.
5. Нельзя включать auto-routing без selective precision ≥ 0.95 на human test.
