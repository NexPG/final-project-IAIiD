# Тесты

```text
tests/
├── test_api.py           # FastAPI, contract, batch, feedback, metrics
├── test_build.py         # 80/20 stratified split, dedup
├── test_labels.py        # TWCS/Bitext mapping
├── test_model_quality.py # model quality, robustness, edge, behavior
├── test_routing.py       # threshold, margin, manual review
├── test_text.py          # cleaning, PII, dedup normalization
└── test_validation.py    # data validation rules
```

## Запуск

```bash
pytest -q
pytest --cov=music_support_triage --cov-report=term-missing
```

## Правила

1. Каждый баг фиксируется тестом.
2. Пограничные случаи из `docs/01_task/TZ.md` покрываются явно.
3. Тесты не ходят в интернет и не требуют реальных PII.
4. Тесты должны проходить на чистом окружении.
5. CI/CD не используется; тесты запускаются локально перед демонстрацией.
