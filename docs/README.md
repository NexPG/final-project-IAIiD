# Документация проекта

Документация разложена по этапам. Внутри каждого раздела — вход, артефакты и проверки.

## 00. Аудит

| Документ | Назначение |
|---|---|
| [`requirements_audit.md`](00_audit/requirements_audit.md) | Проверка задания, плана и 16 вебинаров перед сдачей |

## 01. Задача

| Документ | Назначение |
|---|---|
| [`TZ.md`](01_task/TZ.md) | Техническое задание, источник истины |
| [`sources.md`](01_task/sources.md) | Карта требований: задание, план, 16 вебинаров |
| [`stages.md`](01_task/stages.md) | Этапы 1–6, gates и передача артефактов |
| [`gate_report.md`](01_task/gate_report.md) | Детальный отчёт Gate 1 |
| [`data.md`](01_task/data.md) | Данные, 80/20 split, стратификация |
| [`data_card.md`](01_task/data_card.md) | Data card: источники, split, ограничения |
| [`stage_audit.md`](01_task/stage_audit.md) | Аудит исходных черновиков |

## 02. Архитектура

| Документ | Назначение |
|---|---|
| [`architecture.md`](02_architecture/architecture.md) | Архитектура, компоненты, ADR |
| [`architecture_business.png`](02_architecture/architecture_business.png) | Чистовая бизнес-схема |
| [`architecture.png`](02_architecture/architecture.png) | Техническая схема |
| [`architecture_overview.png`](02_architecture/architecture_overview.png) | Исходный командный набросок |
| [`api.md`](02_architecture/api.md) | API-контракт, ошибки, SLA |
| [`openapi.json`](02_architecture/openapi.json) | OpenAPI-схема |
| [`gate_report.md`](02_architecture/gate_report.md) | Детальный отчёт Gate 2 |

## 03. Эксперименты

| Документ | Назначение |
|---|---|
| [`experiments.md`](03_experiments/experiments.md) | CV, HalvingRandomSearchCV, test, CI |
| [`model_card.md`](03_experiments/model_card.md) | Model card и ограничения |
| [`model_bpmn.png`](03_experiments/model_bpmn.png) | BPMN жизненного цикла модели |
| [`gate_report.md`](03_experiments/gate_report.md) | Детальный отчёт Gate 3: модели, поиск, выбор |

## 04. Тестирование

| Документ | Назначение |
|---|---|
| [`testing.md`](04_testing/testing.md) | Тест-план, model/API tests, найденные проблемы |
| [`gate_report.md`](04_testing/gate_report.md) | Детальный отчёт Gate 4 |

## 05. Деплой

| Документ | Назначение |
|---|---|
| [`deployment.md`](05_deployment/deployment.md) | Docker, Compose, smoke, rollback |
| [`gate_report.md`](05_deployment/gate_report.md) | Детальный отчёт Gate 5 |

## 06. Мониторинг

| Документ | Назначение |
|---|---|
| [`monitoring.md`](06_monitoring/monitoring.md) | Метрики, алерты, drift, runbook |
| [`retrain_bpmn.png`](06_monitoring/retrain_bpmn.png) | BPMN переобучения по дрейфу |
| [`gate_report.md`](06_monitoring/gate_report.md) | Детальный отчёт Gate 6 |

## 07. Отчёт и защита

| Документ | Назначение |
|---|---|
| [`report.md`](07_report/report.md) | Итоговый отчёт 5–7 страниц |
| [`report.pdf`](07_report/report.pdf) · [`report.docx`](07_report/report.docx) | Готовый отчёт |
| [`presentation.md`](07_report/presentation.md) | План презентации 10–15 слайдов |
| [`presentation.pdf`](07_report/presentation.pdf) · [`presentation.pptx`](07_report/presentation.pptx) | Готовая презентация |
| [`speech.md`](07_report/speech.md) | Полная речь для подготовки |
| [`speech_5min.md`](07_report/speech_5min.md) | Короткая речь на 5 минут |

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
