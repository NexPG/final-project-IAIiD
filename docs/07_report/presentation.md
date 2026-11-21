# Презентация: Music Support Triage

**Формат:** 15 слайдов, 5 минут выступления + 2 минуты вопросов.  
**Файлы:** [`presentation.pdf`](presentation.pdf) · [`presentation.pptx`](presentation.pptx) · речь — [`speech_5min.md`](speech_5min.md) и [`speech.md`](speech.md).

Дизайн: короткие тезисы, KPI-карточки, схемы и графики; полный текст выступления — в заметках докладчика и `speech.md`.

## Слайды

1. Титул: Music Support Triage, команда, 7 тем → 7 очередей.
2. Проблема: ручная сортировка, ошибка маршрута, долгий ответ.
3. Задача: вход → модель → тема и очередь, 7 классов, manual_review.
4. Данные: TWCS + Bitext, 13 427 строк, 80/20 stratified, test frozen.
5. Архитектура: бизнес-схема, монолит, online, fallback.
6. Техническая схема: модель, очередь, drift.
7. API: шесть endpoint'ов, пример ответа, SLA, error envelope.
8. Эксперименты: 4 семейства, 120 кандидатов, CV-график.
9. Результат: macro-F1 0.855, KPI-карточки, bootstrap CI.
10. Error analysis: per-class recall, найденный баг с отрицанием.
11. Тестирование: 38 тестов, GE 8/8, dirty 4/8, smoke, load test.
12. Деплой: Docker → image → Compose, KPI, rollback.
13. Мониторинг: 3 уровня, 7 алертов, drift.
14. ИИ-ассистенты: агент — рутина, команда — решения.
15. Ограничения, следующий шаг, команда.

## Ключевые числа

- CV macro-F1: **0.855 ± 0.048**.
- Test macro-F1: **0.855**, 95% CI **[0.791; 0.908]**.
- TWCS отдельно: **0.739**.
- Coverage 0.948, selective precision 0.979.
- 38 тестов; Docker load test p95 52.72 ms.
- 7 алертов; drift PSI 0.003.
