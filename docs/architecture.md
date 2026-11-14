# Архитектура системы

**Статус:** Gate 2 закрыт, v1  
**Источник требований:** [`TZ.md`](TZ.md), §7–§8; вебинары В01–В04  
**Контракт:** [`api.md`](api.md), [`openapi.json`](openapi.json)

## 1. Контекст

Пользователь отправляет обращение в поддержку музыкального сервиса. Backend передаёт текст в сервис классификации и получает тему, confidence, top-k, очередь и флаг ручной проверки. Сервис не отвечает пользователю сам — он только маршрутизирует тикет.

## 2. Ключевые решения

| Вопрос | Решение | Причина |
|---|---|---|
| Монолит или микросервисы | Модульный монолит / один FastAPI-сервис | 5 человек, одна модель, учебная нагрузка |
| Batch или stream | Online-обработка нового тикета; batch-эндпоинт опционально | Нужен ответ при создании обращения |
| Паттерн интеграции | Embedded model в процессе API | Простота, скорость, без сетевой задержки |
| Classical ML или LLM | Classical ML (TF-IDF + LogReg, optional transformer) | Цена, задержка, приватность, детерминизм |
| Human-in-the-loop | Да, при низкой уверенности/margin | Снижение цены ошибки |
| Feature store | Не используем | Одна модель, простые признаки |

## 3. Компоненты

| Компонент | Ответственность |
|---|---|
| Канал / backend | Источник тикета |
| FastAPI API | Валидация, версия, ошибки |
| Preprocessing | Нормализация, очистка, PII |
| Classifier | Вероятности по 7 классам |
| Routing | threshold, margin, очередь, review |
| Feedback | Подтверждение/исправление оператора |
| Monitoring | Метрики, логи, алерты |
| MLflow | Эксперименты и артефакты |

## 4. Схема

```mermaid
flowchart LR
    A[Канал / backend] --> B[FastAPI]
    B --> C[Валидация и нормализация]
    C --> D[PII-маскирование]
    D --> E[Классификатор]
    E --> F[Threshold + margin]
    F --> G[Очередь темы]
    F --> H[Manual review]
    G --> I[Ответ]
    H --> I
    B --> J[Prometheus / logs]
    I --> K[Feedback]
    K --> L[Офлайн-анализ]
    J --> L
    L --> M[Drift / переобучение]
    M --> E
```

## 5. Поток запроса

1. `POST /v1/classify`.
2. Pydantic-валидация.
3. Нормализация текста.
4. PII-маскирование.
5. Инференс.
6. Routing.
7. Ответ + метрики + лог.
8. Feedback (опционально).

## 6. Три узких места

| Узкое место | Последствие отказа | Митигация |
|---|---|---|
| Артефакт модели не загрузился | 503, маршрутизация остановлена | checksum, readiness, rollback, manual queue |
| Backend/очередь недоступна | Тикет не попал в очередь | retry, очередь сообщений, manual fallback |
| Drift входных данных | Тихие ошибки, падение качества | мониторинг, drift-отчёт, переобучение |

## 7. Контракт и SLA

См. [`api.md`](api.md), [`openapi.json`](openapi.json). Обязательные элементы: вход, выход, SLA, ошибки, версия API/модели/данных.

| Ситуация | Поведение |
|---|---|
| Валидный запрос | 200 + `topic`, `queue`, `confidence`, `margin`, `top_k`, `needs_human_review` |
| Ошибка схемы/текста | 422 + `error.code=VALIDATION_ERROR` + `request_id` |
| Модель не загружена | 503 + `error.code=MODEL_UNAVAILABLE` |
| Неизвестный путь | 404 + `error.code=NOT_FOUND` |
| Низкий confidence/margin | 200, `queue=manual_review`, `needs_human_review=true` |
| `other` с высокой уверенностью | 200, `queue=general_support` |

SLA: p95 ≤ 300 мс (TF-IDF), 5xx < 1%, 20 RPS на worker, batch ≤ 100. `request_id` возвращается в теле и заголовке `X-Request-ID`.

## 8. ADR

| ID | Решение | Статус |
|---|---|---|
| ADR-01 | Модульный монолит | accepted |
| ADR-02 | Online-обработка | accepted |
| ADR-03 | Embedded model | accepted |
| ADR-04 | Classical ML без LLM в инференсе | accepted |
| ADR-05 | 7 классов | accepted |
| ADR-06 | Human-in-the-loop | accepted |
| ADR-07 | MLflow локально | accepted |
| ADR-08 | Без GitHub CI/CD | accepted |
| ADR-09 | Без feature store | accepted |
| ADR-10 | Train + StratifiedGroupKFold CV + frozen test | accepted |
| ADR-11 | Threshold/margin по OOF train, не по test | accepted |

## 9. Реализация

| Элемент | Где |
|---|---|
| FastAPI app | `src/music_support_triage/api/app.py` |
| Схемы запроса/ответа | `src/music_support_triage/api/schemas.py` |
| Очистка и PII | `src/music_support_triage/data/text.py` |
| Классификатор | `src/music_support_triage/services/classifier.py` |
| Routing | `src/music_support_triage/services/routing.py` |
| Модель | `src/music_support_triage/models/baseline.py` |
| Метрики | `/metrics`, `monitoring/prometheus.yml` |

**Версионирование:** API — `v1`; модель — `model_version` в артефакте; данные — `dataset_version` (SHA-256) в `data/manifest.json`.

**SLA учебного стенда:** p95 ≤ 300 мс для TF-IDF, 5xx < 1%, readiness через `/healthcheck`. Модель не загружена → 503 и manual fallback.

## 10. Что осталось

- [ ] Human-verified test и финальные метрики (Gate 3).
- [ ] Load test 20 RPS.
- [ ] Grafana dashboard (Prometheus alert rules уже есть).
- [ ] Production-маршрут: reverse proxy, replicas, registry, queue, DB, secrets.
- [ ] Drift-отчёт на реальном потоке (план — `monitoring.md`).
