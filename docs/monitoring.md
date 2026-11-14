# Мониторинг и drift

**Статус:** draft, заполняется на этапе 6  
**Источник требований:** [`TZ.md`](TZ.md), §12; вебинары В12–В13

## 1. Три уровня

| Уровень | Метрики |
|---|---|
| Инфраструктура | latency, throughput, error rate, CPU, RAM, model_loaded |
| Продукт | requests, auto-routed share, review rate, queues |
| Модель | confidence, predicted distribution, override rate, delayed macro-F1, ECE, drift |

## 2. Технические метрики

`http_requests_total`, `http_request_duration_seconds`, `http_errors_total`, `model_inference_seconds`, `batch_size`, `process_cpu_seconds_total`, `process_resident_memory_bytes`, `model_loaded`.

## 3. Метрики данных

`input_length_chars`, `empty_or_short_rate`, `language_mix_rate`, `pii_detected_total`, `duplicate_rate`, `other_share`, `unknown_token_rate`, `drift_psi`, `ks_statistic`.

## 4. Метрики модели

`predicted_topic_total`, `confidence_mean`, `confidence_bucket`, `needs_human_review_rate`, `operator_override_rate`, `macro_f1_delayed`, `selective_precision`, `ece`.

## 5. Алерты

| ID | Условие | Severity | Действие |
|---|---|---|---|
| AL-01 | 5xx > 2% за 5 мин | Critical | Логи, rollback, manual queue |
| AL-02 | p95 > 500 мс за 10 мин | Warning | CPU/RAM, масштабирование |
| AL-03 | `model_loaded=0` | Critical | Артефакт, readiness, перезапуск |
| AL-04 | `other_share` > 25% за 1 час | Warning | Drift, новые темы |
| AL-05 | `confidence_mean` < 0.55 за 30 мин | Warning | Данные/модель |
| AL-06 | `operator_override_rate` > 20% за 24 ч | Critical | Error analysis, переобучение |
| AL-07 | `macro_f1_delayed` < 0.75 | Critical | Rollback, переобучение |
| AL-08 | PII в логах > 0 | Critical | Остановить логи, инцидент |

Пороги — по historical baseline / validation.

## 6. Дашборд

1. Инфраструктура.
2. Продукт.
3. Модель.

## 7. Логирование

Structured JSON:

- timestamp, level, request_id;
- status, latency_ms;
- topic, confidence, queue, model_version;
- PII маскируется.

Middleware на каждый запрос.

## 8. Drift

- Data drift vs concept drift.
- KS-тест, PSI, Evidently.
- Reference: validation / последняя стабильная неделя.
- PSI > 0.2 — сигнал; KS p-value < 0.05 — сигнал.
- Отчёт: Evidently HTML или `docs/drift_report.md`.

## 9. Переобучение

| Стратегия | Когда |
|---|---|
| По расписанию | Медленный дрейф |
| По событию | Сигнал мониторинга |
| Непрерывное | Быстрый дрейф, уровень 2 |

**Решение:** по событию + раз в месяц; только human-verified feedback; не обучаться на своих предсказаниях.

## 10. Демонстрация алерта

Подать поток коротких/нерелевантных текстов → рост `other_share` или падение `confidence_mean` → показать алерт и действие по runbook.
