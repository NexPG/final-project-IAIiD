# Тесты

```text
tests/
├── unit/          # preprocessing, routing, PII, thresholds
├── integration/   # API, batch, feedback, errors
├── contract/      # OpenAPI и схемы ответов
└── data/          # валидация датасета
```

## Запуск

```bash
pytest -q
pytest --cov=music_support_triage --cov-report=term-missing
```

## Правила

1. Каждый баг фиксируется тестом.
2. Пограничные случаи из `docs/TZ.md` (раздел 12.3) покрываются явно.
3. Тесты не ходят в интернет и не требуют реальных PII.
4. Тесты должны проходить на чистом окружении.
5. CI/CD не используется; тесты запускаются локально перед демонстрацией.
