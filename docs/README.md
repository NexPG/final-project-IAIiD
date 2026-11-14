# Документация проекта

Документация разложена по этапам. Внутри каждого раздела — вход, артефакты и проверки.

## 01. Задача

| Документ | Назначение |
|---|---|
| [`TZ.md`](01_task/TZ.md) | Техническое задание, источник истины |
| [`sources.md`](01_task/sources.md) | Карта требований: задание, план, 16 вебинаров |
| [`stages.md`](01_task/stages.md) | Этапы 1–6, gates и передача артефактов |
| [`data.md`](01_task/data.md) | Данные, 80/20 split, стратификация |
| [`data_card.md`](01_task/data_card.md) | Data card: источники, split, ограничения |
| [`stage_audit.md`](01_task/stage_audit.md) | Аудит исходных черновиков |

## 02. Архитектура

| Документ | Назначение |
|---|---|
| [`architecture.md`](02_architecture/architecture.md) | Архитектура, компоненты, ADR |
| [`architecture.png`](02_architecture/architecture.png) | Схема архитектуры |
| [`api.md`](02_architecture/api.md) | API-контракт, ошибки, SLA |
| [`openapi.json`](02_architecture/openapi.json) | OpenAPI-схема |

## 03. Эксперименты

| Документ | Назначение |
|---|---|
| [`experiments.md`](03_experiments/experiments.md) | CV, RandomizedSearchCV, test, CI |
| [`model_card.md`](03_experiments/model_card.md) | Model card и ограничения |

## 04. Тестирование

| Документ | Назначение |
|---|---|
| [`testing.md`](04_testing/testing.md) | Тест-план, model/API tests, найденные проблемы |

## 05. Деплой

| Документ | Назначение |
|---|---|
| [`deployment.md`](05_deployment/deployment.md) | Docker, Compose, smoke, rollback |

## 06. Мониторинг

| Документ | Назначение |
|---|---|
| [`monitoring.md`](06_monitoring/monitoring.md) | Метрики, алерты, drift, runbook |

## 07. Отчёт и защита

| Документ | Назначение |
|---|---|
| [`report.md`](07_report/report.md) | Итоговый отчёт 5–7 страниц |
| [`presentation.md`](07_report/presentation.md) | План презентации 10–15 слайдов |

## 08. ИИ-ассистенты

| Документ | Назначение |
|---|---|
| [`ai_usage.md`](08_ai/ai_usage.md) | Журнал использования ИИ-ассистентов |

## Правила

1. `TZ.md` — единственный источник истины по требованиям.
2. Документы этапов дополняют TZ, но не противоречат ему.
3. Все числа в отчёте и презентации подтверждены артефактами экспериментов.
4. Локальные материалы курса (`docs/project_plan/`, `docs/presentations/`) не входят в репозиторий.
5. Сырые внешние данные лежат в `data/external/` и не коммитятся.
