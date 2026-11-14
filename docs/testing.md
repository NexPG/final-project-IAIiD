# Тестирование и найденные проблемы

**Статус:** draft, заполняется на этапе 4  
**Источник требований:** [`TZ.md`](TZ.md), §10; вебинары В06–В08

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

Минимум 5 expectations:

- `text` not null;
- `label` in 7 classes;
- `split` in train/validation/test;
- `id` unique;
- `scenario_id` не пересекает split;
- длина 10–5000;
- `source` допустим;
- synthetic share в eval = 0;
- PII-проверка;
- достаточно примеров на класс.

Дополнительно: dirty copy, JSON/DataDocs, остановка обучения при провале.

## 3. Model tests (5+ типов)

| Тип | Проверка |
|---|---|
| Overall | macro-F1 ≥ 0.80 |
| Per-class | recall ≥ 0.65 |
| Robustness | uppercase/spaces/punctuation |
| Edge | empty/too long |
| Subgroup | channel/length/language |
| Behavior | negation example |
| Adversarial | typo/synonym |
| Routing | low confidence → manual |

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
- mixed RU/EN, транслит;
- опечатки, сленг;
- HTML/JSON;
- длинный текст;
- несколько тем;
- спам;
- оскорбления;
- PII;
- неподдерживаемый язык;
- дубли;
- обрезанный текст.

## 6. Load test

- 20 RPS, 5 минут.
- 80% валидных, 20% edge.
- p95 ≤ 300/500 мс, 5xx < 1%.
- CPU/RAM.

## 7. Найденная проблема

**Отрицание и конкурирующие признаки.**

Пример: «Подписку отменять не хочу, нужен чек об оплате» → `subscription`, ожидается `payment`.

Требование:

1. Тест воспроизводит.
2. Причина описана.
3. Фикс проверен (данные/char n-grams/transformer/постобработка).
4. Если не исправлено — manual routing и ограничение в отчёте.

Другие известные ограничения:

- старый threshold 0.0;
- confidence не калиброван;
- test 84, по 12 на класс;
- automation disabled.

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
| R-03 | Test 84 | Широкий CI | Human-verified test | open |
| R-04 | PII в логах | Приватность | Маскирование | open |
| R-05 | Модель недоступна | 503 | Readiness/rollback | open |
