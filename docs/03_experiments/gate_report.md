# Gate 3 report: эксперименты

**Этап:** 3. Эксперименты  
**Владелец:** Владимир Егоров  
**Статус:** закрыт  
**Артефакты:** `artifacts/search_results.json`, `artifacts/metrics.json`, `artifacts/model.joblib`, MLflow.

## 1. Вход

- Gate 2: архитектура, API-контракт, OpenAPI.
- Данные: TWCS SpotifyCares + Bitext Customer Support.

## 2. Данные и split

| Источник | Train | Test | Всего |
|---|---|---|---|
| TWCS weak | 4 558 | 1 174 | 5 732 |
| Bitext mapped | 6 155 | 1 540 | 7 695 |
| **Всего** | **10 713** | **2 714** | **13 427** |

- 80/20 split.
- Стратификация одновременно по `(source, label)`.
- Группировка по `conversation_id`.
- Validation не выделяется.
- Test frozen и открыт один раз.

## 3. Какие модели пробовали

| Семейство | Что это | Пространство параметров |
|---|---|---|
| `logreg_word` | TF-IDF word + LogisticRegression | ngram (1,1)/(1,2), min_df 1–3, max_features 20k/50k/100k, sublinear, C 0.5–32, class_weight |
| `logreg_word_char` | TF-IDF word + char_wb + LogisticRegression | word + char (2–5)/(3–5), min_df, max_features, C, class_weight |
| `linear_svc` | TF-IDF + calibrated LinearSVC | ngram, min_df, max_features, C 0.1–4, class_weight |
| `complement_nb` | TF-IDF + ComplementNB | ngram, min_df, max_features, alpha 0.1–2, fit_prior |

## 4. Как обучали

- CV: 5-fold `StratifiedGroupKFold` по `(source, label)`.
- Поиск: `HalvingRandomSearchCV`.
- `n_candidates=120` на семейство.
- `factor=2`, `resource="n_samples"`.
- `min_resources=2000`, `max_resources=8000`.
- 3 раунда: 120 → 60 → 30 кандидатов.
- `scoring="f1_macro"`.
- `random_state=42`.
- После выбора: refit на полном train.
- Порог: рабочий 0.70/0.05; OOF-контроль coverage 0.941, selective precision 0.979.
- Test: один раз.

Итого fits:
- logreg_word: 1 050;
- logreg_word_char: 1 050;
- linear_svc: 1 050;
- complement_nb: 840.

Это в 7–8 раз больше, чем 12 итераций RandomizedSearch.

## 5. Результаты CV

| Семейство | CV macro-F1 | Std | Best params |
|---|---|---|---|
| **logreg_word** | **0.855** | **0.048** | word (1,2), min_df=2, max_features=50k, sublinear=False, C=32, balanced |
| logreg_word_char | 0.848 | 0.038 | word (1,2), min_df=2, max_features=20k; char (2,5), min_df=3, max_features=30k; C=2, balanced |
| linear_svc | 0.775 | 0.012 | word (1,2), min_df=2, max_features=20k, C=2, class_weight=None |
| complement_nb | 0.701 | 0.006 | word (1,2), min_df=1, max_features=50k, alpha=0.1, fit_prior=True |

## 6. Почему выбрали `logreg_word`

1. **Лучший mean CV macro-F1:** 0.855 против 0.848 у word+char.
2. **Проще:** только word-признаки, меньше размер модели и latency.
3. **Word+char не дал убедительного прироста:** +0.007 в пользу word, при этом std у word выше; но по mean word впереди.
4. **SVC и ComplementNB заметно слабее:** 0.775 и 0.701.
5. **Test не использовался для выбора.**

## 7. Финальный test

| Метрика | Значение |
|---|---|
| Accuracy | 0.963 |
| Macro-F1 | **0.855** |
| Weighted-F1 | 0.963 |
| Bootstrap 95% CI | **[0.791; 0.908]** |
| Coverage | 0.948 |
| Selective precision | **0.979** |
| Review rate | 0.052 |

Per-class recall: `payment` 0.97, `subscription` 0.92, `account` 0.96, `app` 0.69, `recommendations` 0.98, `content` 0.40, `other` 0.98.

### Test по источникам (диагностика)

| Источник | Rows | Accuracy | Macro-F1 |
|---|---|---|---|
| Bitext | 1 540 | 0.998 | 0.713 |
| TWCS | 1 174 | 0.917 | 0.739 |

Overall 0.855 смешивает источники; на реальном TWCS macro-F1 = 0.739. Это ограничение, не результат выбора по test.

## 8. Итог Gate 3

- Модели сравнены по CV.
- Гиперпараметры подобраны HalvingRandomSearchCV.
- Test открыт один раз.
- CI опубликован.
- Модель и порог зафиксированы.
- MLflow runs заполнены.
- Gate 3 закрыт.

## 9. Ограничения

- Test-метки weak, не human-verified.
- Overall test смешивает Bitext и TWCS.
- `content` (5 test) и `app` (54 test) редки.
- Bootstrap CI учитывает вариабельность test, не разметку.
- Transformer не запускался: CPU/время; optional.
