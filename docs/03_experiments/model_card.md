# Model card: selected pipeline

**Версия:** `search-logreg_word_char-20261114183117`  
**Дата:** 14.11.2026  
**Владелец:** Владимир Егоров

## 1. Назначение

Классификация обращений поддержки музыкального стриминга в 7 тем и маршрутизация в очередь. Учебный прототип, не production-система.

## 2. Данные

| Параметр | Значение |
|---|---|
| Train | 11 061 |
| Test | 2 786 (20.1%) |
| Источники | TWCS weak 4 570/1 162, Bitext 6 155/1 540, synthetic 336/84 |
| Метки | weak + synthetic |
| Dataset version | `sha256:67759cd75d39af7273785aef5479899ec7748595fa05962a0c65cbc7fd5995a7` |

Объединённый пул перемешан и разделён 80/20 со стратификацией по `(source, label)`. Validation не выделяется: 5-fold CV на train.

## 3. Модель

- Family: `logreg_word_char`.
- TF-IDF word (1,1), `min_df=1`, `max_features=20000`.
- TF-IDF char_wb (3,5), `min_df=3`, `max_features=30000`.
- LogisticRegression, C=16, `class_weight=balanced`, `max_iter=2000`, seed 42.
- Параметры: `RandomizedSearchCV(n_iter=12, cv=5-fold StratifiedGroupKFold, scoring=f1_macro)`.
- Threshold/margin: 0.85 / 0.05 по OOF train.

## 4. Метрики

| Метрика | Значение |
|---|---|
| CV macro-F1 | **0.910 ± 0.011** |
| Test accuracy | 0.959 |
| Test macro-F1 | **0.909** |
| Test weighted-F1 | 0.959 |
| Bootstrap 95% CI для macro-F1 | **[0.876; 0.934]** |
| Test coverage | 0.887 |
| Test selective precision | **0.989** |
| Test review rate | 0.113 |

### Test по источникам (диагностика, не для выбора)

| Источник | Rows | Accuracy | Macro-F1 |
|---|---|---|---|
| Bitext | 1 540 | 0.997 | 0.712 |
| TWCS | 1 162 | 0.912 | 0.680 |
| Synthetic | 84 | 0.905 | 0.906 |

Bitext macro-F1 ниже из-за отсутствующих в его test классов; accuracy высокая. Overall macro-F1 0.909 нельзя интерпретировать как качество только на реальном TWCS.

## 5. Сравнение семейств (CV macro-F1)

| Семейство | CV macro-F1 | Std |
|---|---|---|
| **logreg_word_char** | **0.910** | **0.011** |
| logreg_word | 0.883 | 0.011 |
| linear_svc (calibrated) | 0.870 | 0.011 |
| complement_nb | 0.807 | 0.008 |

Test не использовался для выбора модели или гиперпараметров.

## 6. Ограничения

- Test-метки weak/synthetic, не human-verified.
- Overall test смешивает Bitext, TWCS и synthetic; реальный TWCS macro-F1 ниже.
- Отрицание: «I don't want to cancel my subscription, I need a receipt» → `subscription`, manual_review.
- `content` и `app` редки.
- Synthetic русскоязычный, TWCS/Bitext англоязычные; язык смешан.
- Модель не заменяет оператора; низкая уверенность → manual.

## 7. Воспроизводимость

```bash
python scripts/build_dataset.py --config configs/data.yaml
python scripts/search_models.py --n-iter 12
python scripts/tune_threshold.py
```
