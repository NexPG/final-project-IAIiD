# Тесты

Тесты сгруппированы по назначению.

```text
tests/
├── unit/          # текст, PII, маппинг меток, routing, упаковка
├── data/          # сборка датасета, валидация, split, dedup
├── model/         # качество модели, robustness, edge, subgroup
└── integration/   # FastAPI, contract, batch, feedback, ошибки
```

## Запуск

```bash
pytest -q
pytest tests/unit -q
pytest tests/integration -q
pytest --cov=music_support_triage --cov-report=term-missing
```

## Правила

1. Каждый баг фиксируется тестом.
2. Пограничные случаи из `docs/01_task/TZ.md` покрываются явно.
3. Тесты не ходят в интернет и не требуют реальных PII.
4. Тесты должны проходить на чистом окружении.
5. CI на GitHub Actions запускает `pytest`; локально тесты прогоняются перед демонстрацией.
