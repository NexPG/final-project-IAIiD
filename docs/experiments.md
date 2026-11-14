# Журнал экспериментов

**Статус:** этап 3, CV + RandomizedSearchCV выполнен; test weak/provisional  
**Владелец:** Владимир Егоров  
**Источник требований:** [`TZ.md`](TZ.md), §9; вебинары В05–В07

## 1. Правила

1. Test не используется для выбора модели или гиперпараметров.
2. Модель выбирается по `StratifiedGroupKFold` CV на train.
3. Порог выбирается по OOF-предсказаниям train.
4. Test открывается один раз после фиксации модели и порога.
5. Каждый run логирует params, metrics, artifacts, tags.
6. Фиксируются Git commit, seed, data manifest, версии.
7. Основная метрика — macro-F1; публикуется 95% bootstrap CI.

## 2. Данные

| Компонент | Объём | Роль |
|---|---|---|
| Train | 11 325 | CV, search, refit, OOF-порог |
| Test | 439 | Одно финальное измерение |
| TWCS weak | 4 580 | Реальный домен |
| Bitext mapped | 7 184 | Вспомогательный train |

Validation отдельно не выделяется. Это осознанное решение: CV на train заменяет validation, а test остаётся независимым.

Подробно: [`data.md`](data.md), [`data_card.md`](data_card.md).

## 3. Схема эксперимента

```text
train ── StratifiedGroupKFold(5) ── RandomizedSearchCV (n_iter=12)
   │                                      │
   │                                      ├─ logreg_word
   │                                      ├─ logreg_word_char
   │                                      ├─ linear_svc
   │                                      └─ complement_nb
   │
   ├─ выбрать family + params по mean CV macro-F1
   ├─ refit на полном train
   ├─ OOF-предсказания → threshold/margin
   └─ test один раз → metrics + bootstrap CI
```

`groups=conversation_id` — один диалог не попадает в разные фолды.

## 4. Search space

| Семейство | Ключевые параметры |
|---|---|
| `logreg_word` | ngram (1,1)/(1,2), min_df 1–3, max_features 20k/50k/100k, sublinear, C 0.5–32, class_weight |
| `logreg_word_char` | word + char_wb (2–5)/(3–5), min_df, max_features, C, class_weight |
| `linear_svc` | calibrated LinearSVC, ngram, min_df, C 0.1–4, class_weight |
| `complement_nb` | ngram, min_df, alpha 0.1–2, fit_prior |

`RandomizedSearchCV(n_iter=12, cv=5, scoring="f1_macro", n_jobs=2, random_state=42)`.

## 5. Результаты CV

| Семейство | CV macro-F1 | Std | Выбрано |
|---|---|---|---|
| **logreg_word** | **0.869** | **0.035** | да |
| logreg_word_char | 0.865 | 0.031 | нет |
| linear_svc (calibrated) | 0.807 | 0.038 | нет |
| complement_nb | 0.711 | 0.009 | нет |

Лучшие параметры `logreg_word`: `ngram_range=(1,2)`, `min_df=2`, `max_features=100000`, `sublinear_tf=True`, `C=32`, `class_weight=balanced`.

**Почему не word+char:** CV-разница 0.004 в пределах std; word-only проще и быстрее. Test для выбора не использовался.

## 6. Финальный test (один раз)

| Метрика | Значение |
|---|---|
| Accuracy | 0.920 |
| Macro-F1 | **0.657** |
| Weighted-F1 | 0.916 |
| Bootstrap 95% CI для macro-F1 | **[0.564; 0.739]** |
| Balanced test macro-F1 | 0.680 |
| Test coverage | 0.734 |
| Test selective precision | **0.975** |
| Test review rate | 0.266 |

Per-class recall: `payment` 0.74, `subscription` 0.88, `account` 0.75, `app` 0.83, `recommendations` 0.00, `content` 0.33, `other` 0.97.

**Вывод:** частые классы устойчивы; macro-F1 ограничен редкими классами. `recommendations` (4 test) и `content` (3 test) дают широкий CI и не позволяют делать уверенный per-class вывод. Это ограничение, а не повод удалять классы.

## 7. Threshold и routing

Политика: цель selective precision ≥ 0.95, coverage ≤ 0.90 на OOF, чтобы оставить минимум 10% на manual review.

| Параметр | OOF train | Test |
|---|---|---|
| Threshold / margin | 0.85 / 0.05 | 0.85 / 0.05 |
| Coverage | 0.878 | 0.734 |
| Selective precision | 0.990 | 0.975 |
| Review rate | 0.122 | 0.266 |

Разница OOF/test ожидаема из-за distribution shift. Порог фиксируется в `configs/service.yaml`; после human-verified test пересчитывается.

## 8. Drift train/test

`python scripts/drift_report.py`:

| Показатель | Train | Test |
|---|---|---|
| Средняя длина | 63.9 | 83.4 |
| p95 длины | 132 | 151 |
| Доля `other` | 34.8% | 74.5% |

PSI длины = **0.868**, KS = **0.377**, p < 0.001. Причина — cap `other` в train и естественное распределение test. Следствие: natural test отражает реальный поток, balanced test — редкие классы; публикуются оба.

## 9. Error analysis

- Отрицание: «I don't want to cancel my subscription, I need a receipt» → `subscription`, confidence 0.647, manual_review.
- `content` ↔ `recommendations` confusion: «Please bring back this album» → `recommendations`.
- `recommendations` recall 0 на 4 test.
- `content` recall 0.33 на 3 test.
- `other` доминирует в test (327/439), поэтому weighted-F1 (0.916) выглядит лучше macro-F1 (0.657).

## 10. MLflow

- Tracking URI: `sqlite:///mlflow.db`.
- Experiment: `music_support_triage`.
- Runs: `search_logreg_word`, `search_logreg_word_char`, `search_linear_svc`, `search_complement_nb`, `final_logreg_word`.
- Логируются params, CV mean/std, финальные test-метрики, CI, threshold, coverage.
- Test логируется только в `final_*` run, не в search runs.

## 11. Воспроизводимость

```bash
python scripts/build_dataset.py --config configs/data.yaml
python scripts/search_models.py --n-iter 12
python scripts/tune_threshold.py
python scripts/evaluate.py --split test --balanced --data data/processed/test_balanced.csv
python scripts/drift_report.py
```

## 12. Ограничения

- Test weak → все числа provisional.
- Редкие классы перепредставлены в train (Bitext) и недопредставлены в test (TWCS).
- CV оценивает обобщение внутри train, но не заменяет независимый test.
- Bootstrap CI учитывает только вариабельность test-выборки, не разметку.
- Transformer не запускался: CPU/время; оставлен как optional.

## 13. Историческая справка

Старый черновик на 420 синтетических примерах дал macro-F1 0.929 на 84 тестовых примерах. Эти числа **не являются результатом проекта** и не переносятся в отчёт: они получены на синтетике, по 12 примеров на класс.
