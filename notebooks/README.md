# Ноутбуки

Ноутбуки не являются обязательной частью сдачи: работающий код и воспроизводимые
скрипты лежат в `src/` и `scripts/`.

Если нужна демонстрация в Colab/Jupyter, используйте:

```bash
python scripts/build_dataset.py --config configs/data.yaml
python scripts/search_models.py --n-candidates 120 --factor 2 --min-resources 2000 --max-resources 8000
python scripts/evaluate.py --split test
```

Большие данные не коммитятся; пути берутся из `configs/data.yaml`.
