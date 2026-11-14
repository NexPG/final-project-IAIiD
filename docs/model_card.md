# Model card: TF-IDF + Logistic Regression

**Версия:** `tfidf-logreg-20261114165350`  
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

- Features: TF-IDF word (1–2), `min_df=2`, до 50 000 признаков.
- Classifier: LogisticRegression, C=16, `class_weight=balanced`, max_iter=2000, seed 42.
- Выход: вероятности по 7 классам; routing по threshold 0.70 и margin 0.10.
- ECE top-1 на validation: 0.0845. Подбор предлагает 0.30/0.15 (coverage 0.951, selective precision 0.955), но порог не внедрён до human-verified validation.

## 4. Метрики (provisional)

| Метрика | Validation | Test | Balanced test |
|---|---|---|---|
| Accuracy | 0.939 | 0.913 | 0.807 |
| Macro-F1 | 0.853 | 0.640 | 0.662 |
| Weighted-F1 | 0.939 | 0.910 | 0.793 |

Per-class test recall: `payment` 0.78, `subscription` 0.88, `account` 0.75, `app` 0.72, `recommendations` 0.00, `content` 0.33, `other` 0.96.

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
