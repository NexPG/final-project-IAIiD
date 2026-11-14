# Model card: TF-IDF + Logistic Regression

**Версия:** `tfidf-logreg-20261114162931`  
**Дата:** 14.11.2026  
**Владелец:** Владимир Егоров

## 1. Назначение

Классификация обращений поддержки музыкального стриминга в 7 тем и маршрутизация в очередь. Учебный прототип, не production-система.

## 2. Данные

| Параметр | Значение |
|---|---|
| Train | 11 183 |
| Validation | 327 |
| Test | 439 |
| Источники | TWCS SpotifyCares (4 713), Bitext (7 236) |
| Метки | weak (100%) |
| Dataset version | `sha256:85293186118678f41fcb0465834105a4c4ce2cf2414f3528d7623ee86579829b` |

## 3. Модель

- Features: TF-IDF word (1–2), TF-IDF char_wb (3–5), `min_df=2`, до 50 000 признаков каждого типа.
- Classifier: LogisticRegression, C=4, `class_weight=balanced`, max_iter=2000, seed 42.
- Выход: вероятности по 7 классам; routing по threshold 0.70 и margin 0.10.

## 4. Метрики (provisional)

| Метрика | Validation | Test | Balanced test |
|---|---|---|---|
| Accuracy | 0.930 | 0.916 | 0.833 |
| Macro-F1 | 0.809 | 0.660 | 0.680 |
| Weighted-F1 | 0.929 | 0.914 | 0.817 |

Per-class test recall: `payment` 0.83, `subscription` 0.90, `account` 0.75, `app` 0.89, `recommendations` 0.00, `content` 0.33, `other` 0.95.

**Важно:** test использует weak labels. Числа не финальные.

## 5. Ограничения

- Не понимает отрицания: «I don't want to cancel my subscription, I need a receipt» → `subscription`, confidence 0.647, manual_review.
- Путает `content` и `recommendations`.
- Редкие классы имеют мало примеров и низкий recall.
- Domain shift: train `other` 34.8%, test 74.5%; PSI длины 0.904.
- Не поддерживает русский язык в финальной модели.
- Не заменяет оператора; низкая уверенность → manual.

## 6. Этические заметки

- Публичные твиты могут содержать PII; выполняется маскирование.
- Нельзя использовать модель для дискриминации по языку или каналу.
- Automation bias: интерфейс должен показывать confidence и top-k.
- Модель обучается на исторических данных и может воспроизводить их смещения.

## 7. Воспроизводимость

```bash
python scripts/build_dataset.py --config configs/data.yaml
python scripts/train.py --config configs/baseline.yaml --allow-provisional
python scripts/evaluate.py --split test
```
