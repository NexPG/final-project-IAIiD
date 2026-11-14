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

## Статус

**Этапы 1–3 в работе.** TZ и документация обновлены; собран data pipeline TWCS + Bitext; обучен первый TF-IDF baseline; реализованы FastAPI-сервис, Docker/Compose, Prometheus-метрики и алерты. Метрики пока provisional: validation/test используют weak labels. Следующий шаг — human-verified разметка 300/400 и финальные эксперименты.

Этапы разработки взяты из слайда 3 проектного плана: **Задача → Архитектура → Эксперименты → Тестирование → Деплой → Мониторинг**.

## Что уже реализовано

- 7 классов и маршрутизация в 7 очередей + `manual_review`.
- Data pipeline: загрузка TWCS/Bitext, очистка, PII-маскирование, дедупликация, weak labels, group split, manifest, validation.
- TF-IDF word+char + LogisticRegression; артефакты в `artifacts/`.
- FastAPI: `/v1/classify`, `/v1/classify/batch`, `/v1/feedback`, `/healthcheck`, `/model-info`, `/metrics`.
- 26 тестов, `ruff`, `mypy`, smoke.
- Dockerfile, Compose (api + Prometheus), alert rules.
- Инструкция и скрипты разметки: `docs/annotation.md`.

Подробно: [`docs/stage_audit.md`](docs/stage_audit.md), [`docs/report.md`](docs/report.md).

## Структура репозитория

```text
.
├── configs/                  # конфигурации обучения и сервиса
├── data/                     # локальные данные: raw/interim/processed/feedback
├── docker/                   # Dockerfile и docker-compose (этап 5)
├── docs/                     # TZ, архитектура, API, тесты, деплой, мониторинг
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
`data/external/bitext/`). Для Bitext можно использовать `--fetch-bitext`.

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
pip install -e ".[dev,ml]"

python scripts/download_data.py --config configs/data.yaml
python scripts/build_dataset.py --config configs/data.yaml
python scripts/train.py --config configs/baseline.yaml --allow-provisional
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
```

`--allow-provisional` нужен только пока validation/test размечены weak labels. После human-verified разметки запускайте без него.

## Метрики (provisional)

| Метрика | Validation | Test | Balanced test |
|---|---|---|---|
| Accuracy | 0.930 | 0.916 | 0.833 |
| Macro-F1 | 0.809 | 0.660 | 0.680 |
| Weighted-F1 | 0.929 | 0.914 | 0.817 |

Данные: 11 183 train (TWCS 4 713 + Bitext 7 236), 327 validation, 439 test. Test — weak labels, поэтому числа не финальные. Подробно: [`docs/experiments.md`](docs/experiments.md).

## Документация

- [`docs/TZ.md`](docs/TZ.md) — техническое задание v2.0, источник истины.
- [`docs/sources.md`](docs/sources.md) — карта требований: задание, план, 16 вебинаров.
- [`docs/data.md`](docs/data.md) — план данных, разметки и валидации.
- [`docs/annotation.md`](docs/annotation.md) — аннотационная инструкция и kappa.
- [`docs/stage_audit.md`](docs/stage_audit.md) — аудит текущих черновиков.
- [`docs/architecture.md`](docs/architecture.md) — архитектура и ADR.
- [`docs/api.md`](docs/api.md) — API-контракт.
- [`docs/experiments.md`](docs/experiments.md) — журнал экспериментов.
- [`docs/testing.md`](docs/testing.md) — тест-план и найденные проблемы.
- [`docs/deployment.md`](docs/deployment.md) — локальный запуск и runbook.
- [`docs/monitoring.md`](docs/monitoring.md) — метрики, алерты, drift.
- [`docs/ai_usage.md`](docs/ai_usage.md) — журнал ИИ-ассистентов.
- [`docs/report.md`](docs/report.md) — итоговый отчёт (черновик v0.2).

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

Проект англоязычный: для учебного кейса важнее объём и домен, чем язык.

- **TWCS SpotifyCares** — ~38 тыс. реальных диалогов поддержки Spotify; готовый dev-подкорпус 6 000.
- **Bitext Customer Support** — 26 872 чистых примера, 27 интентов; вспомогательный train.
- **420 синтетических** музыкальных обращений — seed и edge cases.
- **Human-verified validation/test** — 250–300 / 350–400 примеров SpotifyCares.

Цель train — 15 000–20 000 примеров, `other` ≤ 35%, синтетика ≤ 10%. Финальные метрики считаются только на human-verified test. Подробно: [`docs/data.md`](docs/data.md).

## Ограничения

- Учебный прототип, не production-система.
- 7 классов, single-label; несколько тем уходят в manual.
- Англоязычный фокус; русский и mixed-language — опциональное расширение.
- TWCS не имеет официальных тем: train использует слабые метки, их шум честно измеряется.
- `content` и `recommendations` редки в реальном потоке; нужны human-written кейсы и balanced stress subset.
- Нет реальной интеграции с CRM и автоматических ответов.
- CI/CD на GitHub не используется: проверки и запуск локальные.

## Использование ИИ-ассистентов

ИИ-ассистенты применяются только в разработке. Команда проверяет сгенерированный код, данные и текст. Фактический журнал — в [`docs/ai_usage.md`](docs/ai_usage.md).
