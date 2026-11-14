# Скрипты

CLI-скрипты для воспроизводимых операций.

| Скрипт | Назначение |
|---|---|
| `download_data.py` | проверка локальных датасетов и checksums |
| `build_dataset.py` | объединение источников, 80/20 stratified split, manifest |
| `validate_data.py` | схема, дубли, утечки, дисбаланс, PII |
| `validate_data_ge.py` | Great Expectations: 8 expectations; `--dirty` проверяет отлов ошибок |
| `search_models.py` | 5-fold StratifiedGroupKFold + HalvingRandomSearchCV, OOF threshold, bootstrap CI |
| `tune_threshold.py` | показать OOF threshold/margin из результатов поиска |
| `train.py` | обучение выбранной конфигурации |
| `evaluate.py` | метрики на frozen test |
| `export_openapi.py` | выгрузка OpenAPI в docs |
| `drift_report.py` | offline PSI/KS-отчёт |
| `load_test.py` | HTTP load test: RPS, p50/p95/p99, error rate |
| `build_report.py` | DOCX-отчёт из `docs/07_report/report.md` |
| `build_presentation.py` | PPTX-презентация на 15 слайдов |
| `smoke.py` | smoke-проверка запущенного API |

## Порядок

```bash
python scripts/download_data.py --config configs/data.yaml
python scripts/build_dataset.py --config configs/data.yaml
python scripts/validate_data.py --config configs/data.yaml
python scripts/validate_data_ge.py
python scripts/search_models.py --n-candidates 120 --factor 2 --min-resources 2000 --max-resources 8000
python scripts/tune_threshold.py
python scripts/evaluate.py --split test
```

## Правила

1. Скрипты не содержат секретов.
2. Все параметры передаются через аргументы или конфиг.
3. Каждый запуск фиксирует seed и dataset manifest.
4. Сырые данные не коммитятся.
5. Test открывается один раз после фиксации модели и порога.
