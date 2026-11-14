# Журнал экспериментов

**Статус:** этап 3 закрыт; test измерен один раз  
**Владелец:** Владимир Егоров  
**Источник требований:** [`TZ.md`](../01_task/TZ.md), §9; вебинары В05–В07

## 1. Правила

1. TWCS и Bitext объединены в один пул.
2. 80/20 split стратифицирован одновременно по `(source, label)`.
3. Модель выбирается по 5-fold CV на train.
4. Гиперпараметры — `HalvingRandomSearchCV`.
5. Test открывается один раз после фиксации модели и порога.
6. После test дополнительные проверки не используются для выбора.
7. Публикуются CV mean/std, test macro-F1 и 95% bootstrap CI.

## 2. Данные

| Источник | Train | Test | Всего |
|---|---|---|---|
| TWCS weak | 4 558 | 1 174 | 5 732 |
| Bitext mapped | 6 155 | 1 540 | 7 695 |
| **Всего** | **10 713** | **2 714** | **13 427** |

Доли test: TWCS 20.5%, Bitext 20.0%. Классовые доли сохранены.

## 3. Схема эксперимента

```text
combined pool (TWCS + Bitext)
        │
        ├─ deduplicate
        ├─ 80/20 stratified by (source, label), grouped by conversation_id
        │
        ├─ train 10 713 ── 5-fold StratifiedGroupKFold on (source,label)
        │       ├─ HalvingRandomSearchCV: 120 → 60 → 30 candidates
        │       ├─ resource: 2000 → 4000 → 8000 rows
        │       ├─ select by mean CV macro-F1
        │       ├─ refit on full train
        │       └─ OOF threshold/margin
        │
        └─ test 2 714 ── one final evaluation + bootstrap CI
```

## 4. HalvingRandomSearchCV

- `n_candidates=120` на семейство;
- `factor=2`, `resource="n_samples"`;
- `min_resources=2000`, `max_resources=8000`;
- 3 раунда: 120 → 60 → 30 кандидатов;
- `cv=5` (StratifiedGroupKFold по `(source,label)`);
- `scoring="f1_macro"`;
- `random_state=42`.

Итого: 1 050 fits на семейство (кроме ComplementNB — 840), то есть **в 7–8 раз больше**, чем 12 итераций RandomizedSearch.

## 5. Пространства поиска

| Семейство | Параметры |
|---|---|
| `logreg_word` | ngram (1,1)/(1,2), min_df 1–3, max_features 20k/50k/100k, sublinear, C 0.5–32, class_weight |
| `logreg_word_char` | word + char_wb (2–5)/(3–5), min_df, max_features, C, class_weight |
| `linear_svc` | calibrated LinearSVC, ngram, min_df, C 0.1–4, class_weight |
| `complement_nb` | ngram, min_df, alpha 0.1–2, fit_prior |

## 6. Результаты

| Семейство | CV macro-F1 | Std | Best params | Выбрано |
|---|---|---|---|---|
| **logreg_word** | **0.855** | **0.048** | word (1,2), min_df=2, max_features=50k, sublinear=False, C=32, balanced | **да** |
| logreg_word_char | 0.848 | 0.038 | word (1,2), min_df=2, max_features=20k; char (2,5), min_df=3, max_features=30k; C=2 | нет |
| linear_svc | 0.775 | 0.012 | word (1,2), min_df=2, max_features=20k, C=2 | нет |
| complement_nb | 0.701 | 0.006 | word (1,2), min_df=1, max_features=50k, alpha=0.1 | нет |

**Почему выбрана `logreg_word`:**
- максимальный mean CV macro-F1 — 0.855;
- std 0.048 выше, чем у word+char, но разница mean +0.007 и меньшая сложность;
- word-only быстрее и проще для inference;
- word+char не дал статистически убедительного прироста.

## 7. Финальный test (один раз)

| Метрика | Значение |
|---|---|
| Accuracy | 0.963 |
| Macro-F1 | **0.855** |
| Weighted-F1 | 0.963 |
| Bootstrap 95% CI | **[0.791; 0.908]** |
| Coverage | 0.881 |
| Selective precision | **0.989** |
| Review rate | 0.119 |

Per-class recall: `payment` 0.97, `subscription` 0.92, `account` 0.96, `app` 0.69, `recommendations` 0.98, `content` 0.40, `other` 0.98.

### Test по источникам (диагностика)

| Источник | Rows | Accuracy | Macro-F1 |
|---|---|---|---|
| Bitext | 1 540 | 0.998 | 0.713 |
| TWCS | 1 174 | 0.917 | 0.739 |

Overall 0.855 смешивает источники. На реальном TWCS macro-F1 = 0.739; это ограничение, а не выбор по test.

## 8. Threshold и routing

Политика: selective precision ≥ 0.95, coverage ≤ 0.90 на OOF.

| Параметр | OOF | Test |
|---|---|---|
| Threshold / margin | 0.85 / 0.05 | 0.85 / 0.05 |
| Coverage | 0.878 | 0.881 |
| Selective precision | 0.989 | 0.989 |
| Review rate | 0.122 | 0.119 |

## 9. Стабильность split

`python scripts/drift_report.py`:

| Показатель | Train | Test |
|---|---|---|
| Средняя длина | 65.2 | 66.7 |
| p95 длины | 133 | 138 |
| Доля `other` | 44.1% | 44.5% |

PSI длины = **0.003**, KS = **0.020**, p = 0.346 — распределения совпадают, стратификация сработала.

## 10. MLflow

- Tracking: `sqlite:///mlflow.db`.
- Runs: 4 search runs + 1 final run.
- Логируются params, CV mean/std, test macro-F1, CI, coverage, selective precision.
- Test логируется только в final run.

## 11. Воспроизводимость

```bash
python scripts/build_dataset.py --config configs/data.yaml
python scripts/search_models.py --n-candidates 120 --factor 2 --min-resources 2000 --max-resources 8000
python scripts/tune_threshold.py
```

## 12. Ограничения

- Test-метки weak, не human-verified.
- Overall test смешивает источники; TWCS-качество ниже.
- `content` (5 test) и `app` (54 test) редки.
- Bootstrap CI учитывает вариабельность test, не разметку.
- Transformer не запускался: CPU/время; optional.
