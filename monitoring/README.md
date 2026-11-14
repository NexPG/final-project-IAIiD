# Мониторинг

Каталог для конфигурации Prometheus и Grafana. Заполняется на этапе 6.

Планируемые файлы:

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

Описание метрик и runbook — в [`docs/monitoring.md`](../docs/monitoring.md).
