# Model card: selected pipeline

**Версия:** `search-logreg_word-20261114174846`  
**Дата:** 14.11.2026  
**Владелец:** Владимир Егоров

## 1. Назначение

Классификация обращений поддержки музыкального стриминга в 7 тем и маршрутизация в очередь. Учебный прототип, не production-система.

## 2. Данные

| Параметр | Значение |
|---|---|
| Train | 11 004 |
| Test | 1 163 (20% домена TWCS) |
| Источники train | TWCS SpotifyCares 3 725 + Bitext 7 279 |
| Метки | weak (100%) |
| Dataset version | `sha256:fdda88fa7292ac32ba56a09719c7e47531a33042ca805af30f2ffd00ec0763a1` |

Домен TWCS делится 80/20. Bitext добавлен только в train. Validation не выделяется: модель выбирается через `StratifiedGroupKFold` CV на train; test используется один раз.

## 3. Модель

- Family: `logreg_word`.
- Features: TF-IDF word (1–2), `min_df=2`, `max_features=100000`, `sublinear_tf=True`.
- Classifier: LogisticRegression, C=32, `class_weight=balanced`, max_iter=2000, seed 42.
- Параметры выбраны `RandomizedSearchCV` (`n_iter=12`, 5-fold `StratifiedGroupKFold`, scoring=`f1_macro`).
- Threshold/margin: 0.85 / 0.05, выбраны по OOF-предсказаниям train.

## 4. Метрики

| Метрика | Значение |
|---|---|
| CV macro-F1 (train) | **0.875 ± 0.025** |
| Test accuracy | 0.917 |
| Test macro-F1 | **0.726** |
| Test weighted-F1 | 0.916 |
| Bootstrap 95% CI для test macro-F1 | **[0.645; 0.797]** |
| Test coverage (auto-routed) | 0.742 |
| Test selective precision | **0.979** |
| Test review rate | 0.258 |
| Balanced test macro-F1 | 0.760 |

Per-class test recall: `payment` 0.75, `subscription` 0.87, `account` 0.69, `app` 0.82, `recommendations` 0.45, `content` 0.40, `other` 0.96.

**Важно:** test использует weak labels. Числа provisional, но CI и routing-метрики уже показывают профессиональную картину: selective precision 0.979 при coverage 0.742.

## 5. Сравнение семейств (CV macro-F1 на train)

| Семейство | CV macro-F1 | Std |
|---|---|---|
| **logreg_word** | **0.875** | **0.025** |
| logreg_word_char | 0.862 | 0.035 |
| linear_svc (calibrated) | 0.816 | 0.022 |
| complement_nb | 0.704 | 0.011 |

Test не использовался для выбора семейства или гиперпараметров.

## 6. Ограничения

- Не понимает отрицания: «I don't want to cancel my subscription, I need a receipt» → `subscription`, confidence 0.647, manual_review.
- Путает `content` и `recommendations`.
- Редкие классы имеют мало примеров: `recommendations` 11 test, `content` 5 test; их recall нестабилен.
- Domain shift: train `other` 34.7%, test 73.2%; PSI длины 0.883.
- Не поддерживает русский язык в финальной модели.
- Не заменяет оператора; низкая уверенность → manual.

## 7. Этические заметки

- Публичные твиты могут содержать PII; выполняется маскирование.
- Нельзя использовать модель для дискриминации по языку или каналу.
- Automation bias: интерфейс должен показывать confidence и top-k.
- Модель обучается на исторических данных и может воспроизводить их смещения.

## 8. Воспроизводимость

```bash
python scripts/build_dataset.py --config configs/data.yaml
python scripts/search_models.py --n-iter 12
python scripts/tune_threshold.py
python scripts/evaluate.py --split test --balanced --data data/processed/test_balanced.csv
```
