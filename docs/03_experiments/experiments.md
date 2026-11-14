# Журнал экспериментов

**Статус:** этап 3 закрыт; test измерен один раз  
**Владелец:** Владимир Егоров  
**Источник требований:** [`TZ.md`](../01_task/TZ.md), §9; вебинары В05–В07

## 1. Правила

1. Все источники объединены в один пул и разделены 80/20.
2. Split стратифицирован одновременно по `(source, label)`.
3. Модель выбирается по 5-fold CV на train.
4. Гиперпараметры — `RandomizedSearchCV`.
5. Test открывается один раз после фиксации модели и порога.
6. После test дополнительные проверки не используются для выбора.
7. Публикуются CV mean/std, test macro-F1 и 95% bootstrap CI.

## 2. Данные

| Источник | Train | Test | Всего |
|---|---|---|---|
| TWCS weak | 4 570 | 1 162 | 5 732 |
| Bitext mapped | 6 155 | 1 540 | 7 695 |
| Synthetic | 336 | 84 | 420 |
| **Всего** | **11 061** | **2 786** | **13 847** |

Доли test по каждому источнику — 20.0–20.3%. Классовые доли также сохранены.

## 3. Схема

```text
combined pool (TWCS + Bitext + synthetic)
        │
        ├─ deduplicate
        ├─ 80/20 stratified by (source, label), grouped by conversation_id
        │
        ├─ train 11 061 ── 5-fold StratifiedGroupKFold on (source,label)
        │       ├─ RandomizedSearchCV (n_iter=12) per family
        │       ├─ select by mean CV macro-F1
        │       ├─ refit on full train
        │       └─ OOF threshold/margin
        │
        └─ test 2 786 ── one final evaluation + bootstrap CI
```

## 4. Search space

| Семейство | Ключевые параметры |
|---|---|
| `logreg_word` | ngram (1,1)/(1,2), min_df, max_features, C, class_weight |
| `logreg_word_char` | word + char_wb, min_df, max_features, C, class_weight |
| `linear_svc` | calibrated LinearSVC, ngram, min_df, C, class_weight |
| `complement_nb` | ngram, min_df, alpha, fit_prior |

`RandomizedSearchCV(n_iter=12, cv=5, scoring="f1_macro", n_jobs=2, random_state=42)`.

## 5. Результаты CV

| Семейство | CV macro-F1 | Std | Выбрано |
|---|---|---|---|
| **logreg_word_char** | **0.910** | **0.011** | да |
| logreg_word | 0.883 | 0.011 | нет |
| linear_svc (calibrated) | 0.870 | 0.011 | нет |
| complement_nb | 0.807 | 0.008 | нет |

Лучшие параметры: word (1,1), `min_df=1`, `max_features=20000`; char_wb (3,5), `min_df=3`, `max_features=30000`; C=16, `class_weight=balanced`.

**Почему word+char:** CV выше на 0.027 при меньшем std; char-признаки помогают на опечатках и смешанном языке.

## 6. Финальный test (один раз)

| Метрика | Значение |
|---|---|
| Accuracy | 0.959 |
| Macro-F1 | **0.909** |
| Weighted-F1 | 0.959 |
| Bootstrap 95% CI | **[0.876; 0.934]** |
| Coverage | 0.887 |
| Selective precision | **0.989** |
| Review rate | 0.113 |

Per-class recall: `payment` 0.96, `subscription` 0.95, `account` 0.97, `app` 0.86, `recommendations` 0.97, `content` 0.71, `other` 0.97.

### Test по источникам (диагностика)

| Источник | Rows | Accuracy | Macro-F1 |
|---|---|---|---|
| Bitext | 1 540 | 0.997 | 0.712 |
| TWCS | 1 162 | 0.912 | 0.680 |
| Synthetic | 84 | 0.905 | 0.906 |

Overall 0.909 смешивает источники. На реальном TWCS macro-F1 = 0.680; это ограничение, а не выбор по test.

## 7. Threshold и routing

Политика: selective precision ≥ 0.95, coverage ≤ 0.90 на OOF.

| Параметр | OOF | Test |
|---|---|---|
| Threshold / margin | 0.85 / 0.05 | 0.85 / 0.05 |
| Coverage | 0.877 | 0.887 |
| Selective precision | 0.988 | 0.989 |
| Review rate | 0.123 | 0.113 |

## 8. Стабильность split

`python scripts/drift_report.py`:

| Показатель | Train | Test |
|---|---|---|
| Средняя длина | 64.8 | 65.4 |
| p95 длины | 133 | 137 |
| Доля `other` | 43.3% | 43.3% |

PSI длины = **0.002**, KS = **0.012**, p = 0.917 — распределения совпадают, стратификация сработала.

## 9. MLflow

- Tracking: `sqlite:///mlflow.db`.
- Runs: 4 search runs + 1 final run.
- Логируются params, CV mean/std, test macro-F1, CI, coverage, selective precision.
- Test логируется только в final run.

## 10. Воспроизводимость

```bash
python scripts/build_dataset.py --config configs/data.yaml
python scripts/search_models.py --n-iter 12
python scripts/tune_threshold.py
```

## 11. Ограничения

- Test-метки weak/synthetic, не human-verified.
- Overall test смешивает источники; TWCS-качество ниже.
- Synthetic русскоязычный, TWCS/Bitext англоязычные.
- Bootstrap CI учитывает вариабельность test, не разметку.
- Transformer не запускался: CPU/время; optional.
