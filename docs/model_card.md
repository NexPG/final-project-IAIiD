# Model card: selected pipeline

**Версия:** `search-logreg_word-20261114172115`  
**Дата:** 14.11.2026  
**Владелец:** Владимир Егоров

## 1. Назначение

Классификация обращений поддержки музыкального стриминга в 7 тем и маршрутизация в очередь. Учебный прототип, не production-система.

## 2. Данные

| Параметр | Значение |
|---|---|
| Train | 11 325 |
| Test | 439 |
| Источники | TWCS SpotifyCares (4 580), Bitext (7 184) |
| Метки | weak (100%) |
| Dataset version | `sha256:b85ccc381543b4868c277da34a1f3bfae45e60cff1c9e0586b9db6d4cdb150d8` |

Validation отдельно не выделяется. Модель выбирается через `StratifiedGroupKFold` CV на train; test используется один раз после фиксации модели и порога.

## 3. Модель

- Family: `logreg_word`.
- Features: TF-IDF word (1–2), `min_df=2`, `max_features=100000`, `sublinear_tf=True`.
- Classifier: LogisticRegression, C=32, `class_weight=balanced`, max_iter=2000, seed 42.
- Параметры выбраны `RandomizedSearchCV` (`n_iter=12`, 5-fold `StratifiedGroupKFold`, scoring=`f1_macro`).
- Threshold/margin: 0.85 / 0.05, выбраны по OOF-предсказаниям train.

## 4. Метрики

| Метрика | Значение |
|---|---|
| CV macro-F1 (train) | 0.869 ± 0.035 |
| Test accuracy | 0.920 |
| Test macro-F1 | 0.657 |
| Test weighted-F1 | 0.916 |
| Bootstrap 95% CI для test macro-F1 | [0.564; 0.739] |
| Test coverage (auto-routed) | 0.734 |
| Test selective precision | 0.975 |
| Test review rate | 0.266 |
| Balanced test macro-F1 | 0.680 |

Per-class test recall: `payment` 0.74, `subscription` 0.88, `account` 0.75, `app` 0.83, `recommendations` 0.00, `content` 0.33, `other` 0.97.

**Важно:** test использует weak labels. Числа provisional, но CI и routing-метрики уже показывают профессиональную картину: selective precision 0.975 при coverage 0.734.

## 5. Сравнение семейств (CV macro-F1 на train)

| Семейство | CV macro-F1 | Std |
|---|---|---|
| **logreg_word** | **0.869** | **0.035** |
| logreg_word_char | 0.865 | 0.031 |
| linear_svc (calibrated) | 0.807 | 0.038 |
| complement_nb | 0.711 | 0.009 |

Test не использовался для выбора семейства или гиперпараметров.

## 6. Ограничения

- Не понимает отрицания: «I don't want to cancel my subscription, I need a receipt» → `subscription`, confidence 0.647, manual_review.
- Путает `content` и `recommendations`.
- Редкие классы имеют мало примеров и низкий recall.
- Domain shift: train `other` 34.8%, test 74.5%; PSI длины 0.868.
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
