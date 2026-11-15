# Скрипты

CLI-скрипты сгруппированы по этапам проекта. Запуск — из корня репозитория.

```text
scripts/
├── data/          # загрузка, сборка, валидация датасета
├── train/         # обучение, поиск, порог, оценка
├── service/       # smoke, load test, OpenAPI
├── monitoring/    # drift-отчёт
└── report/        # сборка DOCX/PDF, PPTX/PDF, BPMN
```

## data

| Скрипт | Назначение |
|---|---|
| `data/download_data.py` | проверка локальных датасетов и checksums |
| `data/build_dataset.py` | объединение источников, 80/20 stratified split, manifest |
| `data/validate_data.py` | схема, дубли, утечки, дисбаланс, PII |
| `data/validate_data_ge.py` | Great Expectations: 8 expectations; `--dirty` проверяет отлов ошибок |

## train

| Скрипт | Назначение |
|---|---|
| `train/search_models.py` | 5-fold StratifiedGroupKFold + HalvingRandomSearchCV, OOF threshold, bootstrap CI |
| `train/tune_threshold.py` | показать OOF threshold/margin из результатов поиска |
| `train/train.py` | обучение выбранной конфигурации |
| `train/evaluate.py` | метрики на frozen test |

## service

| Скрипт | Назначение |
|---|---|
| `service/smoke.py` | smoke-проверка запущенного API |
| `service/load_test.py` | HTTP load test: RPS, p50/p95/p99, error rate |
| `service/export_openapi.py` | выгрузка OpenAPI в docs |

## monitoring

| Скрипт | Назначение |
|---|---|
| `monitoring/drift_report.py` | offline PSI/KS-отчёт |

## report

| Скрипт | Назначение |
|---|---|
| `report/build_report.py` | DOCX/PDF-отчёт из `docs/07_report/report.md` |
| `report/build_presentation.py` | PPTX/PDF-презентация и заметки докладчика |
| `report/build_bpmn.py` | BPMN-схемы жизненного цикла модели и переобучения |

## Порядок

```bash
python scripts/data/download_data.py --config configs/data.yaml
python scripts/data/build_dataset.py --config configs/data.yaml
python scripts/data/validate_data.py --config configs/data.yaml
python scripts/data/validate_data_ge.py
python scripts/train/search_models.py --n-candidates 120 --factor 2 --min-resources 2000 --max-resources 8000
python scripts/train/tune_threshold.py
python scripts/train/evaluate.py --split test
```

## Правила

1. Скрипты не содержат секретов.
2. Все параметры передаются через аргументы или конфиг.
3. Каждый запуск фиксирует seed и dataset manifest.
4. Сырые данные не коммитятся.
5. Test открывается один раз после фиксации модели и порога.
