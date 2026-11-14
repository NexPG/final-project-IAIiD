# Мониторинг

Реализовано: Prometheus metrics, 7 alert rules, Grafana dashboard.

Файлы:

```text
monitoring/
├── prometheus.yml
├── alerts.yml
└── grafana/
    ├── provisioning/
    └── dashboards/
```

## Требования

- Технические метрики: RPS, errors, latency, CPU, RAM.
- Метрики данных: длина, язык, PII, `other_share`.
- Метрики модели: confidence, review rate, override rate, delayed F1.
- Минимум один алерт с действием.
- Демонстрация алерта на защите.

Проверено: `TriageApiDown` переходит в firing; Grafana provisioning загружает dashboard `Music Support Triage`.

Описание метрик и runbook — в [`docs/06_monitoring/monitoring.md`](../docs/06_monitoring/monitoring.md).
