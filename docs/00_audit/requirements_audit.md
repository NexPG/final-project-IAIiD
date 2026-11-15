# Аудит проекта перед финальной сдачей

**Дата:** 15.11.2026  
**Объект:** репозиторий `final-project-IAIiD`, тема «Классификация обращений в поддержку музыкального сервиса».  
**Источники:** задание курса, `docs/project_plan/Итоговый_проект_курса_Интеграция_ИИ.pdf`, 16 вебинаров `docs/presentations/`, TZ.

## 1. Чек-лист задания

| Требование | Где | Статус |
|---|---|---|
| README с задачей, структурой, запуском/демонстрацией | `README.md` | выполнено |
| Код или Colab-ноутбук | `src/`, `scripts/` | выполнено |
| Тесты или тест-план | `tests/`, `docs/04_testing/testing.md` | выполнено |
| Материалы экспериментов | `docs/03_experiments/`, `artifacts/search_results.json`, MLflow | выполнено |
| Описание архитектуры | `docs/02_architecture/architecture.md`, `architecture_business.png`, `architecture.png` | выполнено |
| API/контракт | `docs/02_architecture/api.md`, `openapi.json` | выполнено |
| Браузерная demo-страница | `/`, `/demo` — HTML поверх `/v1/classify` | выполнено |
| Деплой и мониторинг | `docs/05_deployment/`, `docs/06_monitoring/` | выполнено |
| Отчёт 5–7 страниц | `docs/07_report/report.pdf`, `.docx`, `.md` — 5 страниц PDF | выполнено |
| Презентация 10–15 слайдов | `docs/07_report/presentation.pdf`, `.pptx` — 15 слайдов | выполнено |
| Роли участников | `README.md`, `docs/07_report/report.md`, слайд 15 | выполнено |
| Все материалы доступны по ссылке | публичный GitHub-репозиторий | выполнено |
| ИИ-ассистенты описаны честно | `docs/08_ai/ai_usage.md`, отчёт §10 | выполнено |
| Лицензия проекта | `LICENSE`, MIT, автор NexPG | выполнено |

## 2. Отчёт: 9 пунктов задания

| Пункт | Где | Статус |
|---|---|---|
| Задача и бизнес-контекст | §1 | выполнено |
| Архитектура и компоненты | §3, `architecture.png` | выполнено |
| Обоснование стека | §4 | выполнено |
| ≥3 эксперимента с выводом | §6, 4 семейства + CV | выполнено |
| Валидация данных и тест-план + проблема/риск | §7, `testing.md` | выполнено |
| Деплой/контейнеризация | §8 | выполнено |
| Мониторинг, метрики, ≥1 алерт | §9 | выполнено |
| ИИ-ассистенты: задачи, проверка, исправления | §10 | выполнено |
| Ограничения, drift, этика | §11 | выполнено |

## 3. План проекта (слайд 3)

| Этап | Артефакт | Gate | Статус |
|---|---|---|---|
| 1. Задача | TZ, data, README | закрыт | выполнено |
| 2. Архитектура | architecture, API, OpenAPI | закрыт | выполнено |
| 3. Эксперименты | CV, HalvingRandomSearchCV, test, CI, MLflow | закрыт | выполнено |
| 4. Тестирование | 38 тестов, GE, dirty copy, load | закрыт | выполнено |
| 5. Деплой | Docker, Compose, smoke, rollback | закрыт | выполнено |
| 6. Мониторинг | Prometheus, Grafana, 7 алертов, drift | закрыт | выполнено |

## 4. Вебинары

| Вебинар | Требование | Где | Статус |
|---|---|---|---|
| В01 | 7 этапов ЖЦ, роли, риски | TZ §2.3, `stages.md` | выполнено |
| В02 | схема, монолит/микросервисы, batch/stream, 3 узких места | `architecture.md` | выполнено |
| В03 | контракт, ошибки, SLA, версии | `api.md`, `openapi.json` | выполнено |
| В04 | MLOps, версионирование | TZ, MLflow, data manifest | выполнено |
| В05 | 5+ экспериментов, MLflow, вывод по параметрам | `experiments.md`, Gate 3 report | выполнено |
| В06 | ≥5 проверок, GE, dirty copy, отчёт | `scripts/data/validate_data_ge.py --dirty`, `ge_report*.json` | выполнено |
| В07 | 5+ model tests, robustness, edge, subgroup, behavior, adversarial | `tests/model/test_model_quality.py` | выполнено |
| В08 | unit/integration/mock/contract | `tests/integration/test_api.py`, `tests/README.md` | выполнено (CI/CD — отклонение) |
| В09 | FastAPI, Pydantic, 3+ endpoints, Swagger/TestClient | `api/app.py`, `schemas.py` | выполнено |
| В10 | blue-green/canary/shadow, criteria, rollback | `deployment.md` | выполнено |
| В11 | Dockerfile, Compose api+db, чек-лист | `docker/`, SQLite feedback volume | выполнено (SQLite вместо PostgreSQL) |
| В12 | 3 уровня метрик, dashboard, 3–5 алертов, logs, middleware | Grafana, 7 alerts, `core/logging.py` | выполнено |
| В13 | drift KS/PSI, retraining | `scripts/monitoring/drift_report.py`, `monitoring.md`, `retrain_bpmn.png` | выполнено (Evidently опционален) |
| В14 | GenAI/agents, когда не нужен | ADR-04, отчёт | выполнено |
| В15 | ИИ-ассистент: задачи, проверка, исправления | `ai_usage.md` | выполнено |
| В16 | этика, безопасность, 9 пунктов отчёта | отчёт §10–11, AI checklist | выполнено |

## 5. Найденные и исправленные проблемы аудита

1. **Synthetic был в пуле.** Убран: остались TWCS + Bitext, 13 427 строк.
2. **RandomizedSearchCV с 12 итерациями.** Заменён на `HalvingRandomSearchCV`: 120 кандидатов, factor=2, 3 раунда.
3. **Не было dirty-copy проверки GE.** Добавлен `validate_data_ge.py --dirty`; поймано 4 нарушения.
4. **Не было structured logging.** Добавлен `core/logging.py` + middleware `http_request`.
5. **Не было реальной презентации.** Сгенерированы `presentation.pptx` и `presentation.pdf` на 15 слайдов.
6. **Отчёт не был отдельным файлом.** Сгенерированы `report.docx` и `report.pdf` на 5 страниц.
7. **README не содержал ссылки на сдачу и пример запроса.** Добавлены.
8. **Compose не имел БД.** Feedback переведён на SQLite-volume; production-маршрут PostgreSQL.
9. **Документация была разбросана.** Разложена по `01_task`…`08_ai`, ссылки проверены.
10. **Старые README в `configs/`, `docker/`, `tests/`, `data/`.** Синхронизированы с фактическим состоянием.
11. **Не было лицензии.** Добавлена MIT, автор NexPG.
12. **Model card был неполным.** Добавлены границы применения, мониторинг, переобучение, BPMN и владение.
13. **Не было BPMN.** Добавлены `model_bpmn.png` и `retrain_bpmn.png` с триггерами и rollback.
14. **Скрипты и тесты лежали вперемешку.** Разложены по `scripts/{data,train,service,monitoring,report}` и `tests/{unit,data,model,integration}`; пути и ссылки обновлены.
15. **Презентация была текстовой.** Переработана в визуальный deck: KPI-карточки, схемы, графики, короткие тезисы; добавлена речь по слайдам и заметки докладчика.
16. **Описание ИИ-ассистента было смещено.** Переписано: агент — рутина, команда — решения, проверка и выводы.
17. **Не было браузерной демонстрации.** Добавлена demo-страница `/` и `/demo` на английском; один HTML-файл, без отдельного frontend-билда.

## 6. Осознанные отклонения

| Отклонение | Причина | Компенсация |
|---|---|---|
| CI/CD GitHub не используется | решение команды/учебная среда | локальные `ruff`, `mypy`, `pytest`, smoke |
| 5 человек вместо 3–4 | состав команды | согласовано с преподавателем |
| SQLite вместо PostgreSQL в Compose | учебный стенд | volume + production-маршрут PostgreSQL |
| Evidently не обязателен | достаточно KS/PSI | `drift_report.py` + scipy |
| Test-метки weak | нет human gold | ограничение явно в отчёте; TWCS отдельно 0.739 |
| LLM не используется в инференсе | узкая классификация, цена/латентность | ADR-04, classical ML |

## 7. Итог аудита

Все обязательные пункты задания, проектного плана и 16 вебинаров закрыты. Критические пропуски (dirty-validation, structured logging, реальная презентация, отдельный отчёт, README-ссылки, БД-volume) исправлены. Оставшиеся отклонения осознанны и описаны в отчёте.
