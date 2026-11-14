# Model card: selected pipeline

**Версия:** `search-logreg_word-20261114200534`  
**Дата:** 14.11.2026  
**Владелец:** Владимир Егоров

## 1. Назначение

Классификация обращений поддержки музыкального стриминга в 7 тем и маршрутизация в очередь. Учебный прототип, не production-система.

## 2. Данные

| Параметр | Значение |
|---|---|
| Train | 10 713 |
| Test | 2 714 (20.2%) |
| Источники | TWCS weak 4 558/1 174, Bitext 6 155/1 540 |
| Метки | weak |
| Dataset version | `sha256:42b239bc5ce519377d5709468811188feb236aced991b7bead596b9b13432980` |

Объединённый пул перемешан и разделён 80/20 со стратификацией по `(source, label)`. Validation не выделяется: 5-fold CV на train.

## 3. Модель

- Family: `logreg_word`.
- TF-IDF word (1,2), `min_df=2`, `max_features=50000`, `sublinear_tf=False`.
- LogisticRegression, C=32, `class_weight=balanced`, `max_iter=2000`, seed 42.
- Поиск: `HalvingRandomSearchCV`, 120 кандидатов, factor=2, resources 2000→4000→8000, 5-fold CV.
- Threshold/margin: 0.85 / 0.05 по OOF train.

## 4. Метрики

| Метрика | Значение |
|---|---|
| CV macro-F1 | **0.855 ± 0.048** |
| Test accuracy | 0.963 |
| Test macro-F1 | **0.855** |
| Test weighted-F1 | 0.963 |
| Bootstrap 95% CI для macro-F1 | **[0.791; 0.908]** |
| Test coverage | 0.881 |
| Test selective precision | **0.989** |
| Test review rate | 0.119 |

### Test по источникам (диагностика)

| Источник | Rows | Accuracy | Macro-F1 |
|---|---|---|---|
| Bitext | 1 540 | 0.998 | 0.713 |
| TWCS | 1 174 | 0.917 | 0.739 |

Overall 0.855 смешивает источники; на реальном TWCS macro-F1 = 0.739.

## 5. Сравнение семейств (CV macro-F1)

| Семейство | CV macro-F1 | Std |
|---|---|---|
| **logreg_word** | **0.855** | **0.048** |
| logreg_word_char | 0.848 | 0.038 |
| linear_svc (calibrated) | 0.775 | 0.012 |
| complement_nb | 0.701 | 0.006 |

Test не использовался для выбора модели или гиперпараметров.

## 6. Ограничения

- Test-метки weak, не human-verified.
- Overall test смешивает Bitext и TWCS; реальный TWCS macro-F1 = 0.739.
- Отрицание: «I don't want to cancel my subscription, I need a receipt» → `subscription`, manual_review.
- `content` и `app` редки.
- Модель не заменяет оператора; низкая уверенность → manual.

## 7. Воспроизводимость

```bash
python scripts/build_dataset.py --config configs/data.yaml
python scripts/search_models.py --n-candidates 120 --factor 2 --min-resources 2000 --max-resources 8000
python scripts/tune_threshold.py
```
