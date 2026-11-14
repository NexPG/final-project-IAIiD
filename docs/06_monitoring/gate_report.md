# Gate 6 report: мониторинг

**Этап:** 6. Мониторинг  
**Владелец:** Александр Аксенов  
**Статус:** закрыт

## 1. Что сделано

- `/metrics` с HTTP, model и prediction метриками.
- Prometheus scrape.
- Grafana dashboard `Music Support Triage` с тремя блоками:
  - инфраструктура: request rate, 5xx, p95 latency, model_loaded;
  - продукт: topics, queues, manual review rate;
  - модель: median confidence, confidence distribution.
- 7 alert rules.
- Drift-отчёт PSI/KS.
- Runbook и стратегия переобучения.

## 2. Метрики

- `http_requests_total{method,path,status}`
- `http_request_duration_seconds`
- `model_inference_seconds`
- `model_loaded`
- `predictions_total{topic,queue,needs_review}`
- `prediction_confidence` histogram
- `process_cpu_seconds_total`, `process_resident_memory_bytes`

## 3. Grafana

| Параметр | Значение |
|---|---|
| URL | `http://localhost:3000` |
| Login | `admin` / `admin` |
| Dashboard UID | `music-support-triage` |
| Datasource | Prometheus |
| Provisioning | `monitoring/grafana/` |

Проверено: Grafana healthy, dashboard загружен, панели используют реальные метрики после load test.

## 4. Алерты

| ID | Alert | Условие |
|---|---|---|
| AL-01 | `TriageApiDown` | `up == 0` 2 мин |
| AL-02 | `TriageModelNotReady` | `model_loaded == 0` 1 мин |
| AL-03 | `TriageHigh5xxRate` | 5xx > 1% |
| AL-04 | `TriageHighLatency` | p95 > 500 мс |
| AL-05 | `TriageManualReviewRateHigh` | manual > 30% |
| AL-06 | `TriageOtherShareHigh` | other > 55% |
| AL-07 | `TriageConfidenceLow` | median confidence < 0.60 |

Все 7 правил загружены, health=ok. `TriageApiDown` проверен в firing после остановки api.

## 5. Drift

| Показатель | Train | Test |
|---|---|---|
| Средняя длина | 65.2 | 66.7 |
| p95 длины | 133 | 138 |
| Доля `other` | 44.1% | 44.5% |

PSI = 0.003, KS = 0.020, p = 0.346. Drift на train/test не обнаружен; production drift требует реальных логов.

## 6. Runbook

| Симптом | Действие |
|---|---|
| 503 | Проверить `MODEL_PATH`, artifact, перезапуск |
| 5xx | Rollback, manual queue |
| Latency | CPU/RAM, batch size |
| Manual rate high | Confidence, drift, данные |
| `other` high | Upstream, drift, шаблоны |
| Confidence low | Calibration, drift, версия модели |

## 7. Артефакты

- [`monitoring.md`](monitoring.md)
- `monitoring/prometheus.yml`
- `monitoring/alerts.yml`
- `monitoring/grafana/`
- `scripts/drift_report.py`

## Gate 6

3 уровня метрик, dashboard, 7 алертов, drift-отчёт, runbook.  
**Закрыт.**
