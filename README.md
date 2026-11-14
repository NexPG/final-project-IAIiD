# Music Support Triage

Учебный сквозной ИИ-кейс: **классификация обращений в поддержку музыкального сервиса** и маршрутизация в нужную очередь.

Проект показывает полный инженерный путь: задача → архитектура → эксперименты → тестирование → деплой → мониторинг. Это не коммерческий продукт, а воспроизводимый прототип с честно описанными ограничениями.

## Задача

Пользователи музыкального стримингового сервиса пишут в поддержку через приложение, сайт, email и чат. Обращения вручную сортируют операторы первой линии. Сервис должен по тексту обращения определить тему и направить его в нужную очередь, а при низкой уверенности — на ручную проверку.

**Вход:** текст обращения (опционально — тема письма, канал, язык).  
**Выход:** тема, уверенность, top-k альтернатив, очередь, флаг `needs_human_review`, версия модели.

### Темы и очереди

| Класс | Очередь | Примеры |
|---|---|---|
| `payment` | `billing` | списания, платёжные ошибки, чеки, возвраты |
| `subscription` | `subscriptions` | тариф, продление, отмена, семейный доступ |
| `account` | `account_support` | вход, пароль, 2FA, профиль, безопасность |
| `app` | `technical_support` | плеер, звук, зависания, офлайн, устройства |
| `recommendations` | `recommendations` | персональные подборки, вкусы, лайки |
| `content` | `content_support` | каталог, права, треки, альбомы, метаданные |
| `other` | `general_support` | понятные запросы вне тем: партнёрство, пресса |

Этапы разработки взяты из слайда 3 проектного плана: **Задача → Архитектура → Эксперименты → Тестирование → Деплой → Мониторинг**. Карта этапов и gates — [`docs/01_task/stages.md`](docs/01_task/stages.md).

## Структура репозитория

```text
.
├── configs/                  # конфигурации обучения и сервиса
├── data/                     # локальные данные: raw/interim/processed/feedback
├── docker/                   # Dockerfile и docker-compose (этап 5)
├── docs/                     # документация по этапам 01–08
├── monitoring/               # Prometheus/Grafana (этап 6)
├── notebooks/                # EDA и демонстрационные ноутбуки
├── scripts/                  # train/evaluate/validate
├── src/music_support_triage/ # исходный код сервиса
│   ├── api/                  # FastAPI-роуты и схемы
│   ├── core/                 # конфигурация и логирование
│   ├── data/                 # загрузка, валидация, preprocessing
│   ├── models/               # baseline, transformer, inference
│   ├── monitoring/           # метрики и drift
│   └── services/             # классификация и routing
├── tests/                    # unit/integration/contract tests
├── .env.example
├── .gitignore
├── pyproject.toml
└── README.md
```

## Быстрый старт

Сырые датасеты не коммитятся. Положите TWCS dev/pseudo CSV и Bitext CSV в пути из
[`configs/data.yaml`](configs/data.yaml) (по умолчанию `data/external/twcs/` и
`data/external/bitext/`).

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
pip install -e ".[dev,ml]"

python scripts/download_data.py --config configs/data.yaml
python scripts/build_dataset.py --config configs/data.yaml
python scripts/validate_data_ge.py
python scripts/search_models.py --n-candidates 120 --factor 2 --min-resources 2000 --max-resources 8000
pytest -q
```

Запуск API:

```bash
uvicorn music_support_triage.api.app:app --reload
python scripts/smoke.py
```

Docker:

```bash
docker compose -f docker/docker-compose.yml up --build
# если порт 8000 занят:
$env:API_PORT="8010"; docker compose -f docker/docker-compose.yml up --build
```

## Метрики

| Метрика | Значение |
|---|---|
| CV macro-F1 (5-fold) | 0.855 ± 0.048 |
| Test macro-F1 | 0.855 |
| Bootstrap 95% CI | [0.791; 0.908] |
| Test accuracy | 0.963 |
| Test weighted-F1 | 0.963 |
| Test coverage | 0.881 |
| Test selective precision | 0.989 |

Данные: 13 427 строк, объединённый пул TWCS + Bitext, 80/20 со стратификацией по `(source, label)`: 10 713 train, 2 714 test. Validation не выделяется: 5-fold CV на train, test открывается один раз. Overall macro-F1 0.855 смешивает источники; на реальном TWCS macro-F1 = 0.739. Test-метки weak. Подробно: [`docs/03_experiments/experiments.md`](docs/03_experiments/experiments.md).

## Документация

Документация разложена по этапам:

- [`docs/01_task/`](docs/01_task/) — TZ, источники, stages, data, data card, аудит.
- [`docs/02_architecture/`](docs/02_architecture/) — архитектура, схема, API, OpenAPI.
- [`docs/03_experiments/`](docs/03_experiments/) — эксперименты, model card.
- [`docs/04_testing/`](docs/04_testing/) — тест-план и найденные проблемы.
- [`docs/05_deployment/`](docs/05_deployment/) — Docker, запуск, runbook.
- [`docs/06_monitoring/`](docs/06_monitoring/) — метрики, алерты, drift.
- [`docs/07_report/`](docs/07_report/) — отчёт и презентация.
- [`docs/08_ai/`](docs/08_ai/) — журнал ИИ-ассистентов.

## Команда и роли

| Участник | Этап | Роль |
|---|---|---|
| Максим Федулаев | 2. Архитектура | Архитектор / backend |
| Владимир Егоров | 3. Эксперименты | ML-инженер / data |
| Айдар Мугизов | 4. Тестирование | QA / ML-инженер |
| Евгений Кононов | 5. Деплой | DevOps / backend |
| Александр Аксенов | 6. Мониторинг | MLOps / документация |

Этап 1 «Задача» — вся команда. Распределение утверждено.

## Данные

Все источники объединены в один пул и разделены 80/20 со стратификацией по `(source, label)`:

- **TWCS SpotifyCares** — 5 732 строки, реальный домен.
- **Bitext Customer Support** — 7 695 строк, вспомогательный домен.

Train 10 713, test 2 714. Test-метки weak, поэтому overall 0.855 смешивает источники; на TWCS macro-F1 = 0.739. Подробно: [`docs/01_task/data_card.md`](docs/01_task/data_card.md).

## Ограничения

- Учебный прототип, не production-система.
- 7 классов, single-label; несколько тем уходят в manual.
- Англоязычный фокус; русский и mixed-language — опциональное расширение.
- TWCS не имеет официальных тем: используются слабые метки, их шум честно измеряется.
- Test смешивает TWCS и Bitext; overall macro-F1 выше, чем на TWCS.
- `content` и `app` редки.
- Нет реальной интеграции с CRM и автоматических ответов.
- CI/CD на GitHub не используется: проверки и запуск локальные.

## Использование ИИ-ассистентов

ИИ-ассистенты применяются только в разработке. Команда проверяет сгенерированный код, данные и текст. Фактический журнал — в [`docs/08_ai/ai_usage.md`](docs/08_ai/ai_usage.md).
