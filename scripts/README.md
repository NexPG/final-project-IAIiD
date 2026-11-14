# Скрипты

CLI-скрипты для воспроизводимых операций.

| Скрипт | Назначение |
|---|---|
| `download_data.py` | проверка локальных датасетов, checksums, опциональная загрузка Bitext |
| `build_dataset.py` | сборка train/validation/test, cap `other`, manifest |
| `validate_data.py` | схема, дубли, утечки, дисбаланс, PII |
| `train.py` | обучение TF-IDF + LogReg, model card |
| `evaluate.py` | метрики на validation/test, natural или balanced |
| `make_balanced_test.py` | balanced stress subset |
| `export_annotation_batch.py` | два независимых batch для разметки |
| `merge_annotations.py` | kappa, расхождения, human-verified CSV |
| `smoke.py` | smoke-проверка запущенного API |

## Порядок

```bash
python scripts/download_data.py --config configs/data.yaml
python scripts/build_dataset.py --config configs/data.yaml
python scripts/validate_data.py --config configs/data.yaml
python scripts/train.py --config configs/baseline.yaml --allow-provisional
python scripts/make_balanced_test.py
python scripts/evaluate.py --split test --balanced --data data/processed/test_balanced.csv
```

## Правила

1. Скрипты не содержат секретов.
2. Все параметры передаются через аргументы или конфиг.
3. Каждый запуск фиксирует seed и dataset manifest.
4. Сырые данные не коммитятся.
5. `--allow-provisional` использовать только до human-verified разметки.
