# Итоговый отчёт: Music Support Triage

**Версия:** черновик 0.2, 14.11.2026  
**Команда:** Максим Федулаев, Владимир Егоров, Айдар Мугизов, Евгений Кононов, Александр Аксенов  
**Репозиторий:** https://github.com/NexPG/final-project-IAIiD  
**Data card:** [`data_card.md`](data_card.md) · **Model card:** [`model_card.md`](model_card.md)

> **Статус чисел.** Метрики раздела 4 получены на **weak labels** и являются предварительными. После human-verified разметки validation/test (300/400) таблица обновляется без изменения архитектуры и кода. Все числа воспроизводятся командами из раздела 10.

## 1. Задача и бизнес-контекст

Музыкальный стриминговый сервис получает обращения в поддержку через приложение, сайт, e-mail, чат и Twitter. Первая линия вручную сортирует их по темам, из-за чего растёт время ответа, а часть тикетов попадает не в ту очередь.

Цель проекта — по тексту обращения определить одну из семи тем и предложить очередь маршрутизации. При низкой уверенности обращение уходит на ручную проверку, а не в случайную очередь.

| Класс | Очередь | Пример |
|---|---|---|
| `payment` | `billing` | «Списали дважды», «Где чек?» |
| `subscription` | `subscriptions` | «Отключите автопродление» |
| `account` | `account_support` | «Не приходит код входа» |
| `app` | `technical_support` | «Трек зависает на 10 секунде» |
| `recommendations` | `recommendations` | «Почему мне советуют это?» |
| `content` | `content_support` | «Пропал альбом» |
| `other` | `general_support` | «Хочу предложить сотрудничество» |

**Метрики успеха:** macro-F1 ≥ 0.80 на human-verified test (минимум 0.75 с обоснованием), recall каждого класса ≥ 0.65, selective precision ≥ 0.95, coverage ≥ 0.40, p95 latency ≤ 300 мс.

**Границы:** учебный прототип; нет реальной CRM, автоматических ответов и круглосуточной эксплуатации. Multi-topic обращения уходят в `manual_review`.

## 2. Архитектура

Выбран **модульный монолит** на FastAPI с моделью в процессе API:

```text
Client / CRM
    │ POST /v1/classify
    ▼
FastAPI ── validation ── PII masking ── TF-IDF + LogReg ── routing
    │                                              │
    │                                              ├─ queue (auto)
    │                                              └─ manual_review
    ▼
structured logs + Prometheus /metrics
```

**Почему монолит:** команда 5 человек, один потребитель, небольшая нагрузка. Отдельный model server дал бы лишнюю сетевую и эксплуатационную сложность. В production-маршруте модель можно вынести в model-as-a-service.

**Почему online:** ответ нужен в момент обращения; batch-обработка не подходит для маршрутизации. **Почему classical ML:** TF-IDF + LogReg быстро обучается на CPU, интерпретируем и достаточен для 7 классов; LLM/agent — overengineering для узкой классификации.

**Три узких места:**

1. Модель не загрузилась → все запросы 503; митигация: readiness, checksum, rollback, manual fallback.
2. Очередь/CRM недоступна → тикет не маршрутизируется; митигация: retry и manual queue.
3. Drift входных данных → тихие ошибки; митигация: мониторинг распределений, drift-отчёт, переобучение.

**API:** `POST /v1/classify`, `POST /v1/classify/batch`, `POST /v1/feedback`, `GET /healthcheck`, `GET /model-info`, `GET /metrics`. Ответ содержит `request_id`, тему, очередь, confidence, margin, top-3, флаг `needs_human_review` и версию модели.

## 3. Технологический стек

| Компонент | Выбор | Причина | Альтернатива |
|---|---|---|---|
| Язык | Python 3.12 | ML/NLP-экосистема | — |
| API | FastAPI + Pydantic v2 | OpenAPI, валидация, TestClient | Flask |
| Модель | TF-IDF + LogisticRegression | CPU, скорость, интерпретируемость | LinearSVC, DistilBERT |
| Данные | pandas + PyYAML | Простой воспроизводимый pipeline | Spark |
| Тесты | pytest + httpx | Unit/integration/contract | unittest |
| Деплой | Docker + Compose | Воспроизводимость | venv |
| Мониторинг | Prometheus + alert rules | Стандарт, демонстративно | logs only |

## 4. Эксперименты

### 4.1. Данные

| Источник | Объём | Роль |
|---|---|---|
| TWCS SpotifyCares | 6 000 в dev-подкорпусе, ~38 тыс. в полном | Реальный домен |
| Bitext Customer Support | 26 872, сэмпл 8 000 | Вспомогательный train |
| 420 синтетических | 420 | Seed и edge cases |
| Human-verified | 0 пока | Финальный validation/test |

Собранный train: **11 183** примера (TWCS 4 713 + Bitext 7 236). Validation — 327, test — 439. `other` ограничен 35% в train. Классы: `other` 3 889, `payment` 2 146, `account` 2 061, `subscription` 1 564, `recommendations` 1 286, `app` 219, `content` 18.

### 4.2. Модель

TF-IDF word (1–2) + LogisticRegression, `class_weight=balanced`, C=16, seed 42. Модель выбрана по **balanced validation macro-F1** среди 6 MLflow-запусков; test не использовался для выбора.

| Метрика | Validation | Test | Balanced test (114) |
|---|---|---|---|
| Accuracy | 0.939 | 0.913 | 0.807 |
| Macro-F1 | **0.853** | **0.640** | **0.662** |
| Weighted-F1 | 0.939 | 0.910 | 0.793 |

Сравнение вариантов (validation / test macro-F1): keyword 0.466/0.475, word C=1 0.747/0.563, word C=4 0.818/0.600, **word C=16 0.854/0.640**, char C=4 0.737/0.585, word+char C=4 0.809/0.660. Word+char лучше на test, но хуже на balanced validation, поэтому выбран word C=16; это пример честного выбора без подгонки под test.

**Вывод:** частые классы (`payment`, `subscription`, `other`) работают устойчиво, macro-F1 падает на редких (`recommendations` — 4 примера, recall 0; `content` — 3 примера, recall 0.33). Это ожидаемо для weak labels и дисбаланса. Числа не являются финальными.

**Калибровка и порог.** ECE top-1 = 0.0845. Подбор на validation даёт лучший feasible вариант threshold 0.30 / margin 0.15: coverage 0.951, selective precision 0.955. Формально это лучше текущих 0.70/0.10, но selective precision измерен против weak labels, поэтому порог не внедряется до human-verified validation. В сервисе остаются консервативные 0.70/0.10.

### 4.3. Найденная проблема

**Отрицание и конкурирующие признаки.** Пример: «I don't want to cancel my subscription, I need a receipt» → модель предсказывает `subscription` с confidence 0.647 и отправляет в `manual_review`, хотя ожидается `payment`. Причина: TF-IDF переоценивает слова `cancel/subscription`, не понимая отрицание. Это одновременно баг качества и пример безопасного поведения routing: низкая уверенность не приводит к неверной автоматической маршрутизации.

Дополнительно: «Please bring back this album, it disappeared» → `recommendations` вместо `content`; «I want a feature to improve recommendations» → `other`. Эти ошибки показывают размытость границы `content`/`recommendations` и будут использованы в adversarial/behavior tests.

## 5. Данные, валидация и тестирование

**Pipeline:** download → clean → PII masking → dedup → weak labeling → mapping → group split → manifest → validation.

**Проверки:** обязательные поля, допустимые классы/split/source, длины 10–5000, уникальность id, отсутствие cross-split дублей, отсутствие утечки `conversation_id`, доля `other` ≤ 40%, доля синтетики ≤ 15%, human-verified в eval, PII-паттерны. Отчёт пишется в `data/processed/validation_report.json`. Дополнительно Great Expectations: 8/8 expectations на 11 949 строках (`data/processed/ge_report.json`).

Текущий отчёт: `ok=true`, два предупреждения — provisional eval (766 строк) и низкая поддержка редких классов в test.

**Тесты:** 34 passed. Покрыты очистка/PII, маппинг меток, group split, cap `other`, дедупликация, data validation, routing, API-контракт, batch, feedback idempotency, `/metrics`, model quality (overall, per-class, robustness, edge, behavior, adversarial, subgroup). Локальный quality gate: `ruff`, `mypy`, `pytest`, smoke. Great Expectations: 8/8 проверок на 11 949 строках.

**План финальной проверки:** human-verified validation 300 и test 400, kappa ≥ 0.70, balanced stress subset ≥25 на класс (где возможно), contract test OpenAPI, load test 20 RPS, PII-тест логов, 503 при отсутствии модели.

## 6. Деплой

- Multi-stage `docker/Dockerfile`, slim-образ, non-root пользователь, healthcheck.
- `docker/docker-compose.yml`: API + Prometheus.
- Модель и конфиги монтируются read-only.
- Smoke: `python scripts/smoke.py` проверяет healthcheck, model-info, classify, batch, metrics — 5/5 проверок пройдены и на uvicorn, и в Docker.
- `docker compose build` и `up -d --wait` проверены: api и Prometheus healthy; правила алертов загружены.
- Rollback: предыдущий `model.joblib` + перезапуск контейнера; модель версионируется, артефакт не коммитится.
- CI/CD на GitHub не используется: локальный quality gate и ручной release.

## 7. Мониторинг

**Инфраструктура:** `up`, HTTP 5xx rate, p95 latency, CPU/RAM.
**Продукт:** число запросов, доля auto-routed, доля manual, distribution тем.
**Модель:** `model_loaded`, `model_inference_seconds`, confidence, drift.

Метрики отдаются через `/metrics`. Prometheus scrape-конфиг и 4 алерта: `TriageApiDown`, `TriageModelNotReady`, `TriageHigh5xxRate`, `TriageHighLatency`. Минимальное требование «≥1 алерт» выполнено: после `docker compose stop api` алерт `TriageApiDown` через 2 минуты перешёл в `firing`, после запуска API smoke снова прошёл 5/5.

Drift-план: PSI/KS по длине текста, доле языков, distribution предсказанных тем; Evidently-отчёт; переобучение при устойчивом падении macro-F1 или росте manual rate.

## 8. ИИ-ассистенты

ИИ-ассистенты использовались для:

- аудита и переписывания TZ по 16 вебинарам;
- исследования датасетов и проверки размеров/лицензий;
- генерации каркаса data pipeline, API, тестов и Docker-файлов;
- черновика отчёта и документации.

Что проверено вручную: все команды запущены, тесты и линтеры пройдены, метрики пересчитаны, ссылки на источники сверены. Что не делегировалось: выбор таксономии, разметка, выводы экспериментов, этика и защита. Журнал — `docs/ai_usage.md`.

## 9. Ограничения, drift и этика

- Test пока weak; финальные выводы требуют human-verified разметки.
- TWCS — публичные твиты с шумом, сарказмом, ссылками и PII; PII маскируется, сырые данные не коммитятся.
- Bitext — другой домен (retail/support), поэтому его вес ниже, а оценка идёт только на TWCS.
- `content` и `recommendations` редки; без human-written кейсов их recall ненадёжен.
- Модель не понимает отрицания и сложные multi-topic обращения; такие случаи уходят в manual.
- **Обнаружен distribution shift train/test:** доля `other` 34.8% в train против 74.5% в test; PSI длины 0.904, KS 0.386, p < 0.001. Причина — cap `other` в train и естественное распределение в test. Поэтому публикуются natural и balanced метрики, а `other_share` вынесен в мониторинг.
- Возможен drift: новые темы, язык, длина, каналы. Нужны мониторинг и переобучение.
- Automation bias: оператор не должен слепо доверять топ-1; интерфейс показывает confidence и top-3.
- Лицензия TWCS требует уточнения; данные используются локально в учебных целях.

## 10. Воспроизводимость

```bash
python scripts/download_data.py --config configs/data.yaml
python scripts/build_dataset.py --config configs/data.yaml
python scripts/validate_data.py --config configs/data.yaml
python scripts/validate_data_ge.py
python scripts/run_experiments.py
python scripts/train.py --config configs/baseline.yaml --allow-provisional
python scripts/tune_threshold.py
python scripts/make_balanced_test.py
python scripts/evaluate.py --split test --balanced --data data/processed/test_balanced.csv
python scripts/drift_report.py
uvicorn music_support_triage.api.app:app --port 8000
python scripts/smoke.py
```

**Следующий шаг:** разметить 300 validation и 400 test, пересчитать метрики без `--allow-provisional`, добавить balanced stress subset и обновить раздел 4.

## 11. Роли

| Участник | Этап | Вклад |
|---|---|---|
| Максим Федулаев | 2. Архитектура | Схема, API-контракт, ADR |
| Владимир Егоров | 3. Эксперименты | Данные, pipeline, модель, метрики |
| Айдар Мугизов | 4. Тестирование | Тест-план, pytest, data validation |
| Евгений Кононов | 5. Деплой | Docker, Compose, smoke, rollback |
| Александр Аксенов | 6. Мониторинг | Метрики, алерты, drift, отчёт |
| Вся команда | 1. Задача | TZ, таксономия, данные, защита |
