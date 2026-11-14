# Тестирование и найденные проблемы

**Статус:** базовый набор реализован (37 тестов), финальный тест-план — после human-verified данных  
**Источник требований:** [`TZ.md`](TZ.md), §10; вебинары В06–В08

## 0. Текущий результат

```text
pytest -q   — 37 passed
ruff check . — All checks passed
mypy src     — Success: 19 source files
smoke        — 5/5 (healthcheck, model-info, classify, batch, metrics)
```

Покрыто: очистка/PII, маппинг меток, group split, cap `other`, дедупликация, data validation, routing (threshold/margin/`other`), API-контракт, OpenAPI, error envelope, `X-Request-ID`, batch, feedback idempotency, `/metrics`, model quality (overall macro-F1, per-class recall, robustness, edge, behavior, adversarial, subgroup). Найденные ошибки модели: отрицание («I don't want to cancel my subscription, I need a receipt» → `subscription`), `content`/`recommendations` confusion.

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
- `split` in train/validation/test;
- `id` unique;
- `label_quality` in `human_verified`/`weak`/`synthetic`;
- `conversation_id` не пересекает split;
- длина 10–5000;
- `source` допустим;
- synthetic/weak share в eval = 0;
- `other` ≤ 40% train, synthetic ≤ 15% train;
- PII-проверка;
- достаточно примеров на класс;
- near-duplicates между split = 0.

Дополнительно: dirty copy, JSON/DataDocs, остановка обучения при провале.

## 3. Model tests (5+ типов)

| Тип | Проверка |
|---|---|
| Overall | macro-F1 ≥ 0.80 на natural test, ≥ 0.70 на balanced stress |
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
- твит с @mention и URL;
- цитата трека/исполнителя с нецензурной лексикой.

## 6. Load test

- 20 RPS, 5 минут.
- 80% валидных, 20% edge.
- p95 ≤ 300/500 мс, 5xx < 1%.
- CPU/RAM.

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
| R-02 | Threshold 0.0 | Нет abstention | Калибровка/margin | open |
| R-03 | Старый test 84 | Широкий CI | Human-verified 350–400 | open |
| R-04 | PII в твитах и логах | Приватность | Маскирование, запрет коммита | open |
| R-05 | Модель недоступна | 503 | Readiness/rollback | open |
| R-06 | Шум weak labels TWCS | Низкое качество | Аудит 500, agreement, confidence-фильтр | open |
| R-07 | Дисбаланс `other` | Модель всё относит к `other` | Cap 35%, class weights, macro-F1 | open |
| R-08 | Мало `content`/`recommendations` | Низкий recall | Human-written, balanced stress subset | open |
| R-09 | Неясная лицензия TWCS | Юридический риск | Сырые данные локально, data card | open |
