# Gate 2 report: архитектура

**Этап:** 2. Архитектура  
**Владелец:** Максим Федулаев  
**Статус:** закрыт

## Что сделано

- Выбран модульный монолит FastAPI.
- Online-инференс, embedded model.
- Сравнены монолит/микросервисы, batch/stream, MaaS/embedded, classical ML/LLM.
- 3 узких места: модель, очередь, drift.
- API-контракт: classify, batch, feedback, healthcheck, model-info, metrics.
- Единый error envelope и `X-Request-ID`.
- SLA, версионирование API/модели/данных.
- ADR-01…ADR-11.
- OpenAPI выгружен.
- Схемы:
  - `architecture_business.png` — чистовая бизнес-схема;
  - `architecture_overview.png` — исходный набросок команды;
  - `architecture.png` — техническая D2.

## Артефакты

- [`architecture.md`](architecture.md)
- [`api.md`](api.md)
- [`openapi.json`](openapi.json)
- [`architecture_business.png`](architecture_business.png)
- [`architecture.png`](architecture.png)
- [`architecture_overview.png`](architecture_overview.png)

## Gate 2

Схема читаема, контракт совпадает с кодом, OpenAPI валиден, ошибки и SLA описаны.  
**Закрыт.**
