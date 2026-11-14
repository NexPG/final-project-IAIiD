# Презентация: Music Support Triage

**Формат:** 15 слайдов, выступление 5 минут + 2 минуты вопросов.  
В вебинаре В01 указано 7 минут — уточнить у преподавателя.  
**Файлы:** [`presentation.pdf`](presentation.pdf), [`presentation.pptx`](presentation.pptx).

## Слайды

1. Титул: Music Support Triage, команда.
2. Проблема: ручная сортировка, задержка, ошибки маршрута.
3. Задача: вход, выход, 7 классов, метрики.
4. Данные: TWCS + Bitext, 13 427 строк, 80/20 stratified.
5. Архитектура: общая схема команды.
6. Техническая архитектура: PII, routing, Prometheus, ML-lifecycle.
7. API и routing: endpoints, ошибки, SLA, OpenAPI.
8. Эксперименты: 4 семейства, HalvingRandomSearchCV, CV-график.
9. Финальный test: macro-F1 0.855, CI [0.791; 0.908].
10. Тестирование: 37 тестов, GE, load test, найденный баг.
11. Деплой: Docker/Compose/Grafana, smoke, rollback.
12. Мониторинг: 3 уровня, 7 алертов, drift.
13. ИИ-ассистенты, этика, ограничения.
14. Ограничения и следующий шаг.
15. Команда и роли.

## Ключевые числа

- CV macro-F1: **0.855 ± 0.048**.
- Test macro-F1: **0.855**, 95% CI **[0.791; 0.908]**.
- TWCS отдельно: **0.739**.
- Coverage 0.881, selective precision 0.989.
- 37 тестов; Docker load test p95 52.72 ms.
- 7 алертов; drift PSI 0.003.
