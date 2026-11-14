# Презентация: Music Support Triage

**Формат:** 10–15 слайдов, 5 минут + 2 минуты вопросов (уточнить у преподавателя, если 7 минут).  
**Статус:** черновик v0.1 к защите.

## Слайд 1. Титул

Music Support Triage — классификация обращений в поддержку музыкального сервиса.  
Команда: Максим Федулаев, Владимир Егоров, Айдар Мугизов, Евгений Кононов, Александр Аксенов.

## Слайд 2. Проблема

- Поддержка вручную сортирует тикеты.
- Ошибки маршрутизации → задержка ответа.
- Нужна тема + очередь + безопасный fallback.

## Слайд 3. Задача и метрики

- 7 классов, single-label.
- Вход: текст; выход: тема, confidence, top-3, очередь, review flag.
- Macro-F1, per-class recall, selective precision, coverage, p95 latency.

## Слайд 4. Данные

- TWCS SpotifyCares — реальный домен, ~38 тыс., dev 6 000.
- Bitext — 26 872, вспомогательный train.
- 420 синтетических — seed.
- Train 11 325, test 439.
- Validation не выделяется: 5-fold CV на train.
- Test пока weak → метрики provisional.

## Слайд 5. Архитектура

- Модульный монолит FastAPI.
- Online-инференс, embedded model.
- Preprocessing → TF-IDF/LogReg → routing → queue/manual.
- 3 узких места: модель, очередь, drift.

## Слайд 6. API и routing

- `POST /v1/classify`, batch, feedback.
- `GET /healthcheck`, `/model-info`, `/metrics`.
- threshold 0.70 + margin 0.10 → manual.
- Низкая уверенность не маршрутизируется автоматически.

## Слайд 7. Эксперименты

| Семейство | CV macro-F1 |
|---|---|
| **LogReg word** | **0.869 ± 0.035** |
| LogReg word+char | 0.865 ± 0.031 |
| Calibrated SVC | 0.807 ± 0.038 |
| ComplementNB | 0.711 ± 0.009 |

Выбор по CV на train, не по test. Test: macro-F1 0.657, 95% CI [0.564; 0.739].

## Слайд 8. Ошибки и ограничения

- Отрицание: «I don't want to cancel my subscription, I need a receipt» → `subscription`, manual.
- `content` ↔ `recommendations` confusion.
- `recommendations` recall 0 на 4 тестовых примерах.
- Weak labels и domain shift.

## Слайд 9. Данные и валидация

- PII-маскирование, дедупликация, group split.
- 8/8 Great Expectations.
- 34 теста, `ruff`, `mypy`.
- Drift: PSI длины 0.868, `other_share` 34.8% vs 74.5%.

## Слайд 10. Деплой

- Multi-stage Dockerfile, non-root.
- Compose: api + Prometheus.
- Docker build/up проверены, smoke 5/5.
- Rollback: предыдущий артефакт + перезапуск.

## Слайд 11. Мониторинг

- 3 уровня метрик.
- 4 алерта: API down, model not ready, 5xx, latency.
- `TriageApiDown` проверен в firing.
- Runbook и drift-план.

## Слайд 12. ИИ-ассистенты и этика

- Ассистенты: TZ, данные, код, тесты, отчёт.
- Вручную: таксономия, проверка кода, метрики, выводы.
- PII, bias, automation bias, лицензия TWCS.
- Ограничение: учебный прототип, не production.

## Слайд 13. Следующие шаги

- Human-verified test 400, kappa ≥ 0.70.
- Пересчёт метрик без provisional.
- Balanced stress subset ≥25/класс.
- Contract/load/adversarial тесты.
- Drift на реальных логах.

## Слайд 14. Итог

- Полный путь: задача → архитектура → эксперименты → тесты → деплой → мониторинг.
- Работающий сервис и воспроизводимый pipeline.
- Честно показанные ограничения и следующий шаг.

## Слайд 15. Вопросы

Ссылки: репозиторий, README, report.md, data_card.md, model_card.md.
