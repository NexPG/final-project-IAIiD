# API-контракт

**Статус:** реализовано (v1), этап 2  
**Источник требований:** [`TZ.md`](../01_task/TZ.md), §8; вебинары В03, В09  
**Артефакт:** [`openapi.json`](openapi.json)

## 1. Принципы

- REST, JSON, UTF-8.
- Версия в пути: `/v1`.
- Время ISO 8601 UTC.
- `request_id` в каждом ответе, заголовке `X-Request-ID` и логе.
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
| GET | `/` | Браузерная demo-страница (HTML) | Optional |
| GET | `/demo` | Алиас demo-страницы | Optional |

Demo-страница не входит в OpenAPI-схему: это тонкий UI поверх `POST /v1/classify`.
Она собирается из одного HTML-файла и не требует отдельного frontend-билда.

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
- `channel`: `web`, `email`, `social`, `app`;
- `locale`: `en`, `ru`, `mixed`;
- неизвестные поля запрещены (`extra=forbid`).

## 4. Ответ

```json
{
  "request_id": "6f1c2a3e-7b4d-4f8a-9c1e-2d3b4a5c6d7e",
  "topic": "payment",
  "queue": "billing",
  "confidence": 0.93,
  "margin": 0.89,
  "needs_human_review": false,
  "top_k": [
    {"label": "payment", "confidence": 0.93},
    {"label": "subscription", "confidence": 0.04},
    {"label": "account", "confidence": 0.02}
  ],
  "model_version": "search-logreg_word-20261114172115",
  "latency_ms": 12.4
}
```

Ответ batch:

```json
{
  "request_id": "b4f1...",
  "items": [{"request_id": "...", "topic": "payment", "...": "..."}]
}
```

## 5. Ошибки

Единый конверт:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed",
    "request_id": "6f1c2a3e-7b4d-4f8a-9c1e-2d3b4a5c6d7e",
    "details": []
  }
}
```

| HTTP | Код | Причина |
|---|---|---|
| 404 | `NOT_FOUND` | Неизвестный путь |
| 422 | `VALIDATION_ERROR` | Ошибка схемы/текста/пакета |
| 429 | `RATE_LIMITED` | Лимит (production-маршрут) |
| 500 | `HTTP_ERROR`/`INTERNAL_ERROR` | Непредвиденная ошибка |
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
| 5xx на корректных запросах | < 1% |

## 7. Версионирование

- API: `/v1`, `/v2`; MAJOR ломает совместимость.
- Модель: `model_version` в артефакте и ответе.
- Данные: `dataset_version` + SHA-256 в `data/manifest.json`.
- Пример MINOR: добавлено `top_k`.
- Пример MAJOR: `topic` переименован в `class`.

## 8. Feedback

```json
{
  "request_id": "6f1c2a3e-7b4d-4f8a-9c1e-2d3b4a5c6d7e",
  "correct_topic": "payment",
  "comment": "Подтверждено"
}
```

Идемпотентность по `request_id`: повторный запрос возвращает `already_accepted`.

## 9. Проверки

- [x] OpenAPI валиден (`docs/openapi.json`).
- [x] Contract test.
- [x] 422/503.
- [x] PII не в логах.
- [x] `needs_human_review` по threshold/margin.
- [x] Batch сохраняет порядок.
- [x] `X-Request-ID` в ответе.
