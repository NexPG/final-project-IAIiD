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
| Train | 11 004 | CV, search, refit, OOF-порог |
| Test | 1 163 | 20% домена, одно финальное измерение |
| TWCS weak | 3 725 | Реальный домен |
| Bitext mapped | 7 279 | Вспомогательный train |

Домен TWCS делится 80/20. Bitext добавляется только в train. Validation отдельно не выделяется: CV на train заменяет validation, а test остаётся независимым.

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
| **logreg_word** | **0.875** | **0.025** | да |
| logreg_word_char | 0.862 | 0.035 | нет |
| linear_svc (calibrated) | 0.816 | 0.022 | нет |
| complement_nb | 0.704 | 0.011 | нет |

Лучшие параметры `logreg_word`: `ngram_range=(1,2)`, `min_df=2`, `max_features=100000`, `sublinear_tf=True`, `C=32`, `class_weight=balanced`.

**Почему не word+char:** CV-разница 0.004 в пределах std; word-only проще и быстрее. Test для выбора не использовался.

## 6. Финальный test (один раз)

| Метрика | Значение |
|---|---|
| Accuracy | 0.917 |
| Macro-F1 | **0.726** |
| Weighted-F1 | 0.916 |
| Bootstrap 95% CI для macro-F1 | **[0.645; 0.797]** |
| Balanced test macro-F1 | 0.760 |
| Test coverage | 0.742 |
| Test selective precision | **0.979** |
| Test review rate | 0.258 |

Per-class recall: `payment` 0.75, `subscription` 0.87, `account` 0.69, `app` 0.82, `recommendations` 0.45, `content` 0.40, `other` 0.96.

**Вывод:** частые классы устойчивы; macro-F1 ограничен редкими классами. `recommendations` (11 test) и `content` (5 test) дают широкий CI и не позволяют делать уверенный per-class вывод. Это ограничение, а не повод удалять классы.

## 7. Threshold и routing

Политика: цель selective precision ≥ 0.95, coverage ≤ 0.90 на OOF, чтобы оставить минимум 10% на manual review.

| Параметр | OOF train | Test |
|---|---|---|
| Threshold / margin | 0.85 / 0.05 | 0.85 / 0.05 |
| Coverage | 0.887 | 0.742 |
| Selective precision | 0.989 | 0.979 |
| Review rate | 0.113 | 0.258 |

Разница OOF/test ожидаема из-за distribution shift. Порог фиксируется в `configs/service.yaml`; после human-verified test пересчитывается.

## 8. Drift train/test

`python scripts/drift_report.py`:

| Показатель | Train | Test |
|---|---|---|
| Средняя длина | 62.6 | 86.3 |
| p95 длины | 130 | 176 |
| Доля `other` | 34.7% | 73.2% |

PSI длины = **0.883**, KS = **0.404**, p < 0.001. Причина — cap `other` в train и естественное распределение test. Следствие: natural test отражает реальный поток, balanced test — редкие классы; публикуются оба.

## 9. Error analysis

- Отрицание: «I don't want to cancel my subscription, I need a receipt» → `subscription`, confidence 0.647, manual_review.
- `content` ↔ `recommendations` confusion: «Please bring back this album» → `recommendations`.
- `recommendations` recall 0.45 на 11 test.
- `content` recall 0.40 на 5 test.
- `other` доминирует в test (851/1163), поэтому weighted-F1 (0.916) выглядит лучше macro-F1 (0.726).

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
