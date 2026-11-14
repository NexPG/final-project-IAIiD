# Gate 6 report: мониторинг

**Этап:** 6. Мониторинг  
**Владелец:** Александр Аксенов  
**Статус:** закрыт

## Что сделано

- `/metrics`, Prometheus.
- 4 алерта: API down, model not ready, 5xx, latency.
- `TriageApiDown` проверен в firing.
- Drift-отчёт: PSI 0.003, KS 0.020, `other_share` 44.1% vs 44.5%.
- Runbook и стратегия переобучения.

## Артефакты

- [`monitoring.md`](monitoring.md)
- `monitoring/prometheus.yml`
- `monitoring/alerts.yml`
- `scripts/drift_report.py`

## Gate 6

3 уровня метрик, ≥1 алерт, drift-отчёт, runbook.  
**Закрыт.**
