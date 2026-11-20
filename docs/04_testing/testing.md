# Тестирование и найденные проблемы

**Статус:** реализовано (38 тестов), Gate 4 закрыт  
**Источник требований:** [`TZ.md`](../01_task/TZ.md), §10; вебинары В06–В08

## 0. Текущий результат

```text
pytest -q   — 38 passed
ruff check . — All checks passed
mypy src     — Success: 19 source files
smoke        — 5/5 (healthcheck, model-info, classify, batch, metrics)
Great Expectations — 8/8 clean; dirty copy rejected (4/8 failed)
load test    — 20 RPS, 30 s, 600 requests, 0 errors, p95 9.74 ms
```

Покрыто: очистка/PII, маппинг меток, стратифицированный 80/20 split, дедупликация, data validation, routing (threshold/margin/`other`), API-контракт, OpenAPI, error envelope, `X-Request-ID`, batch, feedback idempotency, `/metrics`, model quality (overall macro-F1, per-class recall, robustness, edge, behavior, adversarial, subgroup). Найденные ошибки модели: отрицание («I don't want to cancel my subscription, I need a receipt» → `subscription`), `content`/`recommendations` confusion.

## 1. Уровни

| Уровень | Что проверяем | Инструмент |
|---|---|---|
| Data | схема, пропуски, дубли, утечки, PII, дисбаланс | pandas + Great Expectations |
| Unit | нормализация, PII, routing, threshold, schema | pytest |
| Model | macro-F1, recall, robustness, edge, subgroup, behavior | pytest |
| Integration | API, batch, feedback, 503, OpenAPI | pytest + TestClient |
| Contract | OpenAPI и ответы | JSON Schema |
| Load | latency, error rate | Locust/k6 |
| E2E | демо-сценарий | чек-лист |

## 2. Data validation

Минимум 8 expectations:

- `text` not null;
- `label` in 7 classes;
- `split` in train/test;
- `id` unique;
- `label_quality` in `weak`;
- `conversation_id` не пересекает split;
- длина 10–5000;
- `source` допустим;
- test без synthetic;
- `other` ≤ 50% train;
- PII-проверка;
- достаточно примеров на класс;
- near-duplicates между split = 0.

Дополнительно: dirty copy, JSON/DataDocs, остановка обучения при провале.

## 3. Model tests (5+ типов)

| Тип | Проверка |
|---|---|
| Overall | macro-F1 ≥ 0.80 на frozen test (факт 0.855) |
| Per-class | recall ≥ 0.65 |
| Robustness | uppercase/spaces/punctuation/handles/URLs |
| Edge | empty/too long/emoji-only |
| Subgroup | channel/length/source |
| Behavior | negation example |
| Adversarial | typo/synonym |
| Routing | low confidence → manual |
| Label noise | ошибки на weak-label subset не скрываются |

## 4. System tests

- Unit preprocessing/postprocessing.
- Integration через TestClient.
- Mock-модель.
- Contract test.
- 503 при недоступной модели.
- Feedback идемпотентен.
- Batch сохраняет порядок.
- PII не в логах.
- OpenAPI доступен.
- `/healthcheck`, `/model-info`, `/metrics`.

## 5. Пограничные случаи

- пустой текст, пробелы, один символ;
- только эмодзи;
- CAPS и повторы;
- mixed EN/RU, транслит;
- опечатки, сленг;
- HTML/JSON;
- длинный текст;
- несколько тем;
- спам;
- оскорбления;
- PII (handle, email, телефон, ссылка);
- неподдерживаемый язык;
- дубли и near-duplicates;
- обрезанный текст;
- пост с @mention и URL;
- цитата трека/исполнителя с нецензурной лексикой.

## 6. Load test

Проведён `scripts/service/load_test.py` против локального API:

| Параметр | Значение |
|---|---|
| Target RPS | 20 |
| Duration | 30 s |
| Requests | 600 |
| Errors | 0 |
| Actual RPS | 20.02 |
| p50 | 7.55 ms |
| p95 | **9.74 ms** |
| p99 | 12.78 ms |
| max | 164.37 ms |

Порог p95 ≤ 500 мс и 5xx < 1% выполнен. CPU/RAM в учебном стенде не измерялись.

## 7. Найденная проблема

**Отрицание и конкурирующие признаки.**

Исторический пример: «Подписку отменять не хочу, нужен чек об оплате» → `subscription`, ожидается `payment`. Английский аналог для нового test: «I don't want to cancel my subscription, I need a receipt» → ожидается `payment`.

Требование:

1. Тест воспроизводит.
2. Причина описана.
3. Фикс проверен (данные/char n-grams/transformer/постобработка).
4. Если не исправлено — manual routing и ограничение в отчёте.

Другие известные ограничения:

- старый threshold 0.0;
- confidence не калиброван;
- старый test 84, по 12 на класс;
- automation disabled;
- weak labels TWCS могут содержать шум;
- `content` и `recommendations` редки в реальном потоке.

## 8. Локальный quality gate

CI/CD не используется.

```bash
ruff check .
ruff format --check .
mypy src
pytest -q
```

Дополнительно:

- `docker compose up` + smoke;
- OpenAPI;
- секреты/PII;
- ignored dirs.

## 9. Risk log

| ID | Проблема | Влияние | Решение | Статус |
|---|---|---|---|---|
| R-01 | Отрицание «не хочу отменять» | Неверная тема | Данные/модель/правило | open |
| R-02 | Threshold 0.0 | Нет abstention | Рабочий порог 0.70/0.05 | closed |
| R-03 | Старый test 84 | Широкий CI | 80/20 frozen test 2 714 | closed |
| R-04 | PII в публичных постах и логах | Приватность | Маскирование, запрет коммита | open |
| R-05 | Модель недоступна | 503 | Readiness/rollback | open |
| R-06 | Шум weak labels | Низкое качество | Ограничение явно указано; confidence-фильтр | accepted |
| R-07 | Дисбаланс `other` | Модель всё относит к `other` | class_weight, macro-F1, стратификация | accepted |
| R-08 | Мало `content`/`app` | Низкий recall | class_weight, macro-F1, стратификация | open |
| R-09 | Неясная лицензия TWCS | Юридический риск | Сырые данные локально, data card | open |
