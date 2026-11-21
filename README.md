# Music Support Triage

[![CI](https://github.com/NexPG/final-project-IAIiD/actions/workflows/ci.yml/badge.svg)](https://github.com/NexPG/final-project-IAIiD/actions/workflows/ci.yml)

Учебный сквозной ИИ-кейс: **классификация обращений в поддержку музыкального сервиса** и маршрутизация в нужную очередь.

Проект показывает полный инженерный путь: задача → архитектура → эксперименты → тестирование → деплой → мониторинг. Это не коммерческий продукт, а воспроизводимый прототип с честно описанными ограничениями.

## Материалы сдачи

- [Отчёт (PDF)](docs/07_report/report.pdf) · [DOCX](docs/07_report/report.docx) · [Markdown](docs/07_report/report.md)
- [Презентация (PDF)](docs/07_report/presentation.pdf) · [PPTX](docs/07_report/presentation.pptx)
- [Model card](docs/03_experiments/model_card.md)
- [BPMN жизненного цикла](docs/03_experiments/model_bpmn.png) · [BPMN переобучения](docs/06_monitoring/retrain_bpmn.png)
- [Роли команды](#команда-и-роли) · [Журнал ИИ-ассистентов](docs/08_ai/ai_usage.md)

## Задача

Пользователи музыкального стримингового сервиса пишут в поддержку через сайт, email, социальные сети и приложения. Обращения вручную сортируют операторы первой линии. Сервис должен по тексту обращения определить тему и направить его в нужную очередь, а при низкой уверенности — на ручную проверку.

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
├── .github/workflows/ci.yml  # CI: ruff, mypy, pytest
├── configs/                  # конфигурации обучения и сервиса
├── data/                     # локальные данные: raw/interim/processed/feedback
├── docker/                   # Dockerfile и docker-compose (этап 5)
├── docs/                     # документация по этапам 00–08
├── monitoring/               # Prometheus/Grafana (этап 6)
├── scripts/
│   ├── data/                 # загрузка, сборка, валидация
│   ├── train/                # поиск, обучение, порог, оценка
│   ├── service/              # smoke, load test, OpenAPI
│   ├── monitoring/           # drift-отчёт
│   └── report/               # отчёт, презентация, BPMN
├── src/music_support_triage/ # исходный код сервиса
│   ├── api/                  # FastAPI-роуты, схемы и demo-страница
│   ├── core/                 # конфигурация и логирование
│   ├── data/                 # загрузка, валидация, preprocessing
│   ├── models/               # baseline, transformer, inference
│   ├── monitoring/           # метрики и drift
│   └── services/             # классификация и routing
├── tests/
│   ├── unit/                 # текст, PII, маппинг, routing
│   ├── data/                 # сборка, split, validation
│   ├── model/                # качество и robustness
│   └── integration/          # API, contract, feedback
├── .env.example
├── .gitignore
├── LICENSE
├── pyproject.toml
└── README.md
```

## Быстрый старт

Модель и сырые данные **не коммитятся**. Чистый клон сначала скачивает данные и
обучает финальную модель скриптом — без подбора гиперпараметров, на уже выбранном
кандидате.

### 1. Окружение

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
pip install -e ".[dev]"
```

### 2. Данные

```bash
# Bitext — публичный Hugging Face
python scripts/data/download_data.py --fetch-bitext

# TWCS — официальный Kaggle API, нужен Kaggle API token
# Windows PowerShell:
$env:KAGGLE_USERNAME="your_username"
$env:KAGGLE_KEY="your_api_key"
# Linux/macOS:
# export KAGGLE_USERNAME=your_username
# export KAGGLE_KEY=your_api_key

python scripts/data/download_data.py --fetch-twcs
python scripts/data/prepare_twcs.py
```

`prepare_twcs.py` собирает из raw `twcs.csv` файлы `dev_cases.csv` и
`dev_cases_pseudo_labeled.csv`. Формат и источники описаны в
[`data/external/README.md`](data/external/README.md).

### 3. Обучение финальной модели

```bash
python scripts/data/build_dataset.py --config configs/data.yaml
python scripts/data/validate_data_ge.py
python scripts/train/train_final.py
pytest -q
```

`train_final.py` использует заранее выбранные параметры: TF-IDF word (1,2),
`min_df=2`, `max_features=50000`, LogReg C=32, `class_weight=balanced`.
Никакого поиска и подбора на этом шаге нет.

### 4. Запуск API

```bash
uvicorn music_support_triage.api.app:app --reload
python scripts/service/smoke.py
```

После старта открыть **http://127.0.0.1:8000/**.

## Demo page

After starting the API, open **http://127.0.0.1:8000/** (or `/demo`).
The page is in English: type a support message, press **Find my queue**, and it shows the
recommended queue, topic, confidence, top alternatives and whether a human review is needed.

The page calls `POST /v1/classify` from the same origin, so no separate frontend build,
Node.js or external services are required. The same page is available in Docker after
`docker compose up` at `http://127.0.0.1:8000/`.

Демонстрация одного запроса:

```bash
curl -X POST http://127.0.0.1:8000/v1/classify \
  -H "Content-Type: application/json" \
  -d "{\"text\":\"I was charged twice for my subscription\",\"channel\":\"app\"}"
```

Ответ содержит `topic`, `queue`, `confidence`, `margin`, `top_k` и
`needs_human_review`; при confidence < 0.70 или margin < 0.05 очередь будет
`manual_review`.

Docker (после шага 3, когда модель обучена и `artifacts/model.joblib` существует):

```bash
docker compose -f docker/docker-compose.yml up --build
# если порт 8000 занят:
$env:API_PORT="8010"; docker compose -f docker/docker-compose.yml up --build
```

Grafana: `http://localhost:3000` (`admin` / `admin`), dashboard `Music Support Triage`.

## CI

GitHub Actions workflow [`.github/workflows/ci.yml`](.github/workflows/ci.yml) runs on every
push to `main` and on pull requests:

```bash
ruff check .
mypy src
pytest -q
```

Docker build, smoke and release remain local: CI checks code quality and tests, not deployment.

## Метрики

| Метрика | Значение |
|---|---|
| CV macro-F1 (5-fold) | 0.855 ± 0.048 |
| Test macro-F1 | 0.855 |
| Bootstrap 95% CI | [0.791; 0.908] |
| Test accuracy | 0.963 |
| Test weighted-F1 | 0.963 |
| Test coverage | 0.948 |
| Test selective precision | 0.979 |

Данные: 13 427 строк, объединённый пул TWCS + Bitext, 80/20 со стратификацией по `(source, label)`: 10 713 train, 2 714 test. Validation не выделяется: 5-fold CV на train, test открывается один раз. Overall macro-F1 0.855 смешивает источники; на реальном TWCS macro-F1 = 0.739. Test-метки weak. Подробно: [`docs/03_experiments/experiments.md`](docs/03_experiments/experiments.md).

## Документация

Документация разложена по этапам:

- [`docs/00_audit/`](docs/00_audit/) — финальный аудит задания, плана и вебинаров.
- [`docs/01_task/`](docs/01_task/) — TZ, источники, stages, data, data card.
- [`docs/02_architecture/`](docs/02_architecture/) — архитектура, схема, API, OpenAPI.
- [`docs/03_experiments/`](docs/03_experiments/) — эксперименты, model card, BPMN жизненного цикла.
- [`docs/04_testing/`](docs/04_testing/) — тест-план и найденные проблемы.
- [`docs/05_deployment/`](docs/05_deployment/) — Docker, запуск, runbook.
- [`docs/06_monitoring/`](docs/06_monitoring/) — метрики, алерты, drift, BPMN переобучения.
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

Этап 1 «Задача» — вся команда. Распределение ролей утверждено.

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
- CI на GitHub Actions: `ruff`, `mypy`, `pytest` на каждый push и pull request; Docker-сборка и release — локально.

## Использование ИИ-ассистентов

ИИ-ассистент применялся к рутинным задачам: шаблонный код, склейка шагов pipeline в единый запуск, черновики автотестов, прогон проверок и поиск багов. Задачи, данные, таксономию, архитектуру, эксперименты, выводы и защиту делала команда. Каждый сгенерированный фрагмент проверялся запуском кода, тестами и сверкой с артефактами. Фактический журнал — в [`docs/08_ai/ai_usage.md`](docs/08_ai/ai_usage.md).
