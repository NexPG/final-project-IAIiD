# Структура итогового отчёта

**Требование:** 5–7 страниц.  
**Статус:** заполняется к защите.  
**Источник:** задание курса, [`TZ.md`](TZ.md), вебинар В16.

## 1. Задача и бизнес-контекст (0.5–0.75 стр.)

- Проблема ручной сортировки.
- Пользователи и очереди.
- Метрики успеха.
- Границы решения.

## 2. Архитектура и компоненты (1–1.25 стр.)

- Схема.
- Поток запроса.
- API-контракт.
- ADR: монолит, online, embedded, classical ML, 7 классов.
- 3 узких места.
- Human-in-the-loop.

## 3. Технологический стек (0.5–0.75 стр.)

- Python, FastAPI, Pydantic.
- TF-IDF/LogReg, optional transformer.
- MLflow, Great Expectations, pytest.
- Docker Compose, Prometheus/Grafana.
- Почему выбран каждый компонент.

## 4. Эксперименты (1–1.5 стр.)

Не менее трёх вариантов:

| Эксперимент | Гипотеза | Результат | Вывод |
|---|---|---|---|
| E0 | Keyword baseline | TBD | TBD |
| E1 | TF-IDF word | TBD | TBD |
| E2 | TF-IDF word+char | TBD | TBD |
| E3 | LinearSVC/CNB | TBD | TBD |
| E4 | Calibration/threshold | TBD | TBD |
| E5 | TWCS vs TWCS+Bitext | TBD | TBD |
| E6 | Cap `other` / class weights | TBD | TBD |
| E7 | Transformer (optional) | TBD | TBD |

Обязательно: macro-F1 на natural и balanced stress test, per-class recall, coverage, selective precision, latency, вывод. Отдельно — agreement слабых меток.

## 5. Данные и тестирование (1–1.25 стр.)

- Источники: TWCS SpotifyCares (~38 тыс., реальный домен), Bitext (26 872, вспомогательный), 420 синтетических (seed).
- Почему английский язык допустим для учебного проекта.
- Train 15 000–20 000: слабые метки TWCS + Bitext + синтетика; `other` ≤ 35%.
- Human-verified validation 300 и test 400; balanced stress subset.
- Разметка и kappa; agreement слабых меток.
- Data validation (8+ GE).
- Тест-план.
- Найденная проблема: отрицание/конкуренция признаков.
- Что исправлено и что осталось.

## 6. Деплой и контейнеризация (0.5–0.75 стр.)

- Dockerfile, Compose.
- Smoke.
- Стратегия shadow/canary/rollback.
- Честный учебный маршрут.
- Production-маршрут.

## 7. Мониторинг (0.75–1 стр.)

- 3 уровня метрик.
- 3–5 алертов.
- Drift: KS/PSI/Evidently.
- Переобучение.
- Runbook.

## 8. ИИ-ассистенты (0.5 стр.)

- Задачи.
- Что проверено.
- Что исправлено.
- Что не делегировалось.

## 9. Ограничения, drift, этика (0.5–0.75 стр.)

- Ограничения прототипа.
- Шум слабых меток TWCS и доменный сдвиг Bitext.
- Дисбаланс `other`, редкие `content`/`recommendations`.
- Drift.
- PII, bias, fairness, transparency.
- Automation bias.
- Следующий шаг.

## Требования

- Все числа подтверждены артефактами.
- Не выдавать синтетические метрики и старые 0.929 за реальные.
- Указать, что train использует слабые метки, а test — human-verified.
- Указать отклонение: CI/CD не используется.
- Указать роли 5 участников в финальном распределении.
- Объём 5–7 страниц без приложений.
