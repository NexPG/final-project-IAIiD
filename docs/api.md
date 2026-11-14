# API-контракт

**Статус:** draft, заполняется на этапе 2  
**Источник требований:** [`TZ.md`](TZ.md), §8; вебинары В03, В09

## 1. Принципы

- REST, JSON, UTF-8.
- Версия в пути: `/v1`.
- Время ISO 8601 UTC.
- `request_id` в каждом ответе и логе.
- Единый формат ошибок.
- OpenAPI: `/openapi.json`, `/docs`.
- Версии API, модели и данных — отдельно.

## 2. Эндпоинты

| Метод | Путь | Назначение | Статус |
|---|---|---|---|
| POST | `/v1/classify` | Классификация одного обращения | Must |
| POST | `/v1/classify/batch` | Пакет до 100 | Should |
| POST | `/v1/feedback` | Обратная связь оператора | Should |
| GET | `/healthcheck` | Liveness/readiness | Must |
| GET | `/model-info` | Версия модели, метрики, пороги | Must |
| GET | `/metrics` | Prometheus | Must |

## 3. Запрос

```json
{
  "text": "I was charged for a subscription I cancelled yesterday.",
  "subject": "Duplicate charge",
  "channel": "app",
  "locale": "en"
}
```

Ограничения:

- `text`: 10–5000;
- `subject`: 0–300;
- `channel`: `twitter`, `app`, `web`, `email`, `chat`;
- `locale`: `en`, `ru`, `mixed`;
- неизвестные поля запрещены.

## 4. Ответ

```json
{
  "request_id": "6f1c2a3e-7b4d-4f8a-9c1e-2d3b4a5c6d7e",
  "topic": "payment",
  "confidence": 0.93,
  "top_k": [
    {"topic": "payment", "confidence": 0.93},
    {"topic": "subscription", "confidence": 0.04},
    {"topic": "account", "confidence": 0.02}
  ],
  "queue": "billing",
  "needs_human_review": false,
  "model": {
    "name": "tfidf-logreg",
    "version": "1.0.0",
    "trained_at": "2026-11-20T10:00:00Z",
    "confidence_threshold": 0.70,
    "margin_threshold": 0.10
  },
  "processed_at": "2026-11-20T10:05:12Z"
}
```

## 5. Ошибки

```json
{
  "error": {
    "code": "TEXT_TOO_SHORT",
    "message": "Поле text должно содержать не менее 10 символов",
    "request_id": "6f1c2a3e-7b4d-4f8a-9c1e-2d3b4a5c6d7e"
  }
}
```

| HTTP | Код | Причина |
|---|---|---|
| 400 | `BAD_REQUEST` | Некорректный JSON |
| 422 | `VALIDATION_ERROR` | Ошибка схемы |
| 422 | `TEXT_TOO_SHORT` | < 10 символов |
| 422 | `TEXT_TOO_LONG` | > 5000 символов |
| 422 | `BATCH_TOO_LARGE` | > 100 |
| 429 | `RATE_LIMITED` | Лимит |
| 500 | `INTERNAL_ERROR` | Непредвиденная ошибка |
| 503 | `MODEL_UNAVAILABLE` | Модель не загружена |

## 6. SLA

| Параметр | Значение |
|---|---|
| p95 latency | ≤ 300 мс для TF-IDF, ≤ 500 мс общий |
| p99 | ≤ 1000 мс |
| Throughput | ≥ 20 RPS на worker |
| Max text | 5000 |
| Batch | 100 |
| Rate limit | 10 RPS |
| Timeout | 10 с |

## 7. Версионирование

- API: `/v1`, `/v2`; MAJOR ломает совместимость.
- Модель: `MAJOR.MINOR.PATCH`.
- Данные: `dataset_version` + SHA-256.
- Пример MINOR: добавлено `top_k`.
- Пример MAJOR: `topic` переименован в `class`.

## 8. Feedback

```json
{
  "request_id": "6f1c2a3e-7b4d-4f8a-9c1e-2d3b4a5c6d7e",
  "predicted_topic": "payment",
  "actual_topic": "payment",
  "operator_id": "op-42",
  "comment": "Подтверждено"
}
```

Идемпотентность по `request_id + operator_id`.

## 9. Проверки

- [ ] OpenAPI валиден.
- [ ] Contract test.
- [ ] 422/503.
- [ ] PII не в логах.
- [ ] `needs_human_review` по threshold/margin.
- [ ] Batch сохраняет порядок.
