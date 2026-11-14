# Gate 4 report: тестирование

**Этап:** 4. Тестирование  
**Владелец:** Айдар Мугизов  
**Статус:** закрыт

## Что проверено

- Data validation: pandas + 8/8 Great Expectations; dirty copy rejected.
- Unit: очистка, PII, маппинг, split, dedup, routing.
- Model: overall, per-class, robustness, edge, behavior, adversarial, subgroup.
- API: contract, batch, feedback, 422/503, OpenAPI, error envelope.
- Smoke: 5/5.
- Load: 20 RPS / 30 s / 600 requests, 0 errors, p95 9.74 ms.

## Результат

```text
pytest -q   — 37 passed
ruff        — passed
mypy        — passed
GE          — 8/8
load test   — 20 RPS, 30 s, 600 requests, 0 errors, p95 9.74 ms
```

## Найденные проблемы

- Отрицание: «I don't want to cancel my subscription, I need a receipt» → `subscription`, manual_review.
- `content`/`recommendations` confusion.
- Test смешивает Bitext и TWCS; на TWCS macro-F1 ниже.

## Артефакты

- [`testing.md`](testing.md)
- `tests/`
- `data/processed/ge_report.json`

## Gate 4

Критические сценарии покрыты, найденная проблема описана, quality gate зелёный.  
**Закрыт.**
