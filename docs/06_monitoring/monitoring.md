# Мониторинг и drift

**Статус:** Gate 6 закрыт: метрики, Prometheus, Grafana, алерты, drift, runbook  
**Источник требований:** [`TZ.md`](../01_task/TZ.md), §12; вебинары В12–В13

## 1. Три уровня

| Уровень | Метрики |
|---|---|
| Инфраструктура | latency, throughput, error rate, CPU, RAM, model_loaded |
| Продукт | requests, auto-routed share, review rate, queues |
| Модель | confidence, predicted distribution, override rate, delayed macro-F1, ECE, drift |

## 2. Технические метрики

`http_requests_total`, `http_request_duration_seconds`, `model_inference_seconds`, `model_loaded`, `process_cpu_seconds_total`, `process_resident_memory_bytes`.

## 3. Метрики данных

`input_length_chars`, `empty_or_short_rate`, `language_mix_rate`, `pii_detected_total`, `duplicate_rate`, `other_share`, `unknown_token_rate`, `drift_psi`, `ks_statistic`.

## 4. Метрики модели

`predictions_total{topic,queue,needs_review}`, `prediction_confidence` histogram, `model_loaded`, `model_inference_seconds`.  
Delayed macro-F1 / selective precision / ECE считаются офлайн и публикуются в отчёте, а не в runtime.

## 5. Алерты

| ID | Alert | Условие | Severity | Действие |
|---|---|---|---|---|
| AL-01 | `TriageApiDown` | `up == 0` 2 мин | Critical | Проверить контейнер, логи, перезапуск |
| AL-02 | `TriageModelNotReady` | `model_loaded == 0` 1 мин | Critical | Артефакт, readiness, rollback |
| AL-03 | `TriageHigh5xxRate` | 5xx > 1% за 5 мин | Warning | Логи, rollback, manual queue |
| AL-04 | `TriageHighLatency` | p95 > 500 мс за 5 мин | Warning | CPU/RAM, batch size |
| AL-05 | `TriageManualReviewRateHigh` | manual review > 30% за 10 мин | Warning | Confidence, drift, данные |
| AL-06 | `TriageOtherShareHigh` | `other` > 55% за 10 мин | Warning | Drift, upstream, шаблоны |
| AL-07 | `TriageConfidenceLow` | median confidence < 0.60 | Warning | Calibration, drift, версия модели |

Реализовано в `monitoring/alerts.yml`; Prometheus подключает rules через `prometheus.yml`. Все 7 правил загружены и health=ok. Пороги учебные; в production калибруются по historical baseline.

## 6. Дашборд Grafana

- URL: `http://localhost:3000`;
- логин/пароль: `admin` / `admin`;
- dashboard: `Music Support Triage`, uid `music-support-triage`;
- provisioning: `monitoring/grafana/`;
- datasource: Prometheus (`http://prometheus:9090`).

Блоки:

1. **Инфраструктура:** request rate, 5xx rate, p95 latency, `model_loaded`.
2. **Продукт:** predictions by topic, routing queues, manual review rate.
3. **Модель:** median confidence, распределение confidence, drift — офлайн-отчёт.

Проверено: Grafana healthy, dashboard загружен через provisioning, панели используют реальные `predictions_total` и `prediction_confidence_bucket`.

## 7. Логирование

Реализовано в `src/music_support_triage/core/logging.py` и middleware `app.py`.

Structured JSON:

- timestamp, level, request_id;
- method, path, status, latency_ms;
- PII маскируется до логирования.

Middleware пишет `http_request` на каждый запрос.

## 8. Drift

- Data drift vs concept drift.
- KS-тест, PSI, Evidently.
- Reference: OOF train / последняя стабильная неделя.
- PSI > 0.2 — сигнал; KS p-value < 0.05 — сигнал.
- Отчёт: `python scripts/drift_report.py` → `artifacts/drift_report.json`.

**Первый offline-отчёт (train vs test):** PSI длины 0.003, KS 0.020, p = 0.346; `other_share` 44.1% vs 44.5%. Стратифицированный 80/20 split сохранил распределения, поэтому drift на train/test не обнаружен. Production drift требует реальных логов.

## 9. Переобучение

| Стратегия | Когда |
|---|---|
| По расписанию | Медленный дрейф |
| По событию | Сигнал мониторинга |
| Непрерывное | Быстрый дрейф, уровень 2 |

**Решение:** по событию + раз в месяц; только подтверждённый feedback; не обучаться на своих предсказаниях.

## 10. Демонстрация алерта

1. Запустить `docker compose -f docker/docker-compose.yml up --build`.
2. Открыть Prometheus `http://localhost:9090/alerts`.
3. Остановить api или подать поток ошибок → `TriageApiDown` / `TriageHigh5xxRate` переходит в firing.
4. Выполнить действие по runbook: проверить `/healthcheck`, логи, перезапустить контейнер, при необходимости откатить модель.

**Проверено:** `docker compose stop api` → через 2 минуты `TriageApiDown` перешёл в `firing`; после `docker compose start api` smoke снова 5/5.

## 11. Runbook

| Симптом | Проверка | Действие |
|---|---|---|
| 503 на classify | `/healthcheck`, `model_loaded` | Проверить `MODEL_PATH`, артефакт, перезапустить |
| Рост 5xx | логи, `http_requests_total` | Rollback, manual queue |
| Рост latency | CPU/RAM, размер batch | Уменьшить batch, увеличить CPU, перезапустить |
| Падение confidence | распределение тем, drift | Error analysis, переобучение |
