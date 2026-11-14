# Журнал экспериментов

**Статус:** план v2; старые runs — только исторический baseline  
**Владелец:** Владимир Егоров (этап 3)  
**Источник требований:** [`TZ.md`](TZ.md), §9; вебинары В05–В07

## 1. Правила

1. Test не используется для подбора гиперпараметров.
2. Validation — только human-verified SpotifyCares.
3. Слабые метки TWCS и синтетика — только train.
4. Каждый run логирует params, metrics, artifacts, tags.
5. Фиксируются Git commit, seed, data manifest, версии.
6. Вывод по каждому эксперименту обязателен.
7. Основная метрика — macro-F1 на human-verified test; отдельно публикуется balanced stress subset.

## 2. Исторический baseline (не финальный)

Черновик этапа 3 дал 6 MLflow runs на **420 синтетических примерах**:

| Запуск | Признаки | C | Macro-F1 val | Macro-F1 test | Accuracy test |
|---|---|---|---|---|---|
| Keyword baseline | keywords | — | 0.748 | 0.837 | 0.833 |
| Words | word | 0.5 | 0.726 | 0.704 | 0.702 |
| Words | word | 4.0 | 0.722 | 0.739 | 0.738 |
| Words | word | 16.0 | 0.735 | 0.750 | 0.750 |
| Words + chars | word_char | 4.0 | 0.917 | 0.929 | 0.929 |
| Words + chars | word_char | 16.0 | 0.904 | 0.929 | 0.929 |

**Важно:** test 84 примера, по 12 на класс, данные синтетические. Эти числа **не являются финальными** и не переносятся в отчёт как результат проекта. Они показывают только, что пайплайн MLflow и модель работают. На реальном TWCS ожидается заметно более низкий и более честный результат.

### 2.1. Первый run на новых данных (provisional)

Дата: 14.11.2026. Модель: TF-IDF word (1–2) + char_wb (3–5), LogisticRegression, `class_weight=balanced`, C=4.

| Параметр | Значение |
|---|---|
| Train | 11 183 |
| Validation | 327 |
| Test | 439 |
| Источники train | TWCS weak 4 713 + Bitext mapped 7 236 |
| `other` в train | ≤ 35% после cap |
| Метка test | weak (provisional) |

| Метрика | Validation | Test | Balanced test (114) |
|---|---|---|---|
| Accuracy | 0.930 | 0.916 | 0.833 |
| Macro-F1 | 0.809 | 0.660 | 0.680 |
| Weighted-F1 | 0.929 | 0.914 | 0.817 |

**Вывод:** на естественном test macro-F1 падает из-за редких классов. `recommendations` имеет 0 recall (4 примера), `content` — 0.33 recall (3 примера), `account` — 0.75, `app` — 0.89. `payment`, `subscription`, `other` работают устойчиво (F1 0.84–0.96). Это ожидаемый результат для слабых меток и сильного дисбаланса, а не финальная оценка.

**Ограничение:** test использует weak labels, поэтому числа нельзя защищать как финальные. Нужна human-verified разметка и balanced stress subset с ≥25 примерами на класс.

## 3. Данные для новых экспериментов

| Компонент | Объём | Роль |
|---|---|---|
| TWCS SpotifyCares weak | до 12 000 | Основной train |
| Bitext mapped | 6 000–8 000 | Вспомогательный train, вес 0,5 |
| Synthetic | 420 | Seed и редкие классы |
| Human-verified train | 300–500 | Дополнительный сигнал |
| Validation | 300 | Подбор порогов |
| Test natural | 400 | Финальная оценка |
| Test balanced stress | 25–30/класс | Проверка редких классов |

Подробно: [`data.md`](data.md).

## 4. Целевые эксперименты

| ID | Гипотеза | Конфигурация | Что сравниваем | Статус |
|---|---|---|---|---|
| E0 | Keyword baseline — нижняя граница на реальных данных | эвристики | macro-F1, latency | План |
| E1 | TF-IDF word + LogReg лучше keyword | C=0.5/4/16 | macro-F1, per-class recall | План |
| E2 | Char n-grams помогают на опечатках и коротких твитах | word+char, C=4/16 | macro-F1, robustness | План |
| E3 | LinearSVC/CNB конкурентен и быстрее | TF-IDF + LinearSVC/CNB | macro-F1, скорость | План |
| E4 | Калибровка + threshold/margin повышают selective precision | CalibratedClassifierCV | coverage, selective precision, ECE | План |
| E5 | Bitext улучшает редкие классы | TWCS vs TWCS+Bitext | macro-F1, per-class recall | План |
| E6 | Ограничение `other` и class weights помогают | cap 35% + balanced | macro-F1, `other` share | План |
| E7 (optional) | Transformer/embeddings лучше на перефразированиях | DistilBERT или MiniLM + LogReg | macro-F1, latency, размер | Опционально |

Минимум: 3 варианта, 5+ MLflow runs. Цель: 7–9 runs на новом split.

### 4.1. Обязательные абляции

1. **TWCS only** vs **TWCS + Bitext** — нужен ли внешний домен.
2. **Weak labels only** vs **weak + human-verified train** — сколько даёт ручная разметка.
3. **Без cap `other`** vs **cap 35%** — как дисбаланс влияет на macro-F1.
4. **Natural test** vs **balanced stress subset** — не маскирует ли `other` провал редких классов.

## 5. Метрики

| Метрика | Цель | Комментарий |
|---|---|---|
| Macro-F1 (natural test) | ≥ 0.80 | Основная; минимум 0.75 с анализом |
| Macro-F1 (balanced stress) | ≥ 0.70 | Честная проверка редких классов |
| Recall каждого класса | ≥ 0.65 | Кроме `other`, если обосновано |
| Selective precision | ≥ 0.95 | Среди auto-routed |
| Coverage | ≥ 0.40 | Доля auto-routed |
| Review rate | ≤ 0.60 | Доля manual |
| ECE | ≤ 0.10 | После калибровки |
| p95 latency | ≤ 300 мс | TF-IDF CPU |
| Model size | ≤ 500 МБ | Для демо |
| Weak-label agreement | ≥ 0.70 | Аудит 500 примеров |

Если цель не достигнута — error analysis + объяснение + следующий шаг. Не подгонять test.

## 6. MLflow

- Experiment: `music_support_triage`.
- Run name: `<model>-<dataset_version>-<seed>`.
- Params: model, C, ngram_range, seed, dataset_version, threshold, class_weight, other_cap, bitext_weight.
- Metrics: val/test macro-F1, accuracy, per-class recall, coverage, selective precision, ECE, latency, weak-label agreement.
- Artifacts: model, confusion matrix, classification report, config, data manifest.
- Tags: `code_sha256`, `dataset_sha256`, `owner`, `stage`, `label_quality`.

## 7. Error analysis

- confusion matrix на natural и balanced test;
- top-30 ошибок;
- разбивка по классам, длине, источнику, языку;
- `other` и неоднозначные;
- отрицания;
- опечатки, сленг, эмодзи, ссылки;
- калибровка;
- ошибки, вызванные слабыми метками;
- вывод и следующий шаг.

## 7.1. Дрейф train/test

`python scripts/drift_report.py` на текущем датасете:

| Показатель | Train | Test |
|---|---|---|
| Средняя длина | 63.1 | 83.4 |
| p95 длины | 131 | 151 |
| Доля `other` | 34.8% | 74.5% |

PSI длины = 0.904, KS = 0.386, p < 0.001. Это не случайный шум: train намеренно cap-ает `other` до 35%, а test сохраняет естественное распределение. Следствие: модель учится на сбалансированном train, но проверяется на реальном смещённом потоке. Это правильно для оценки, но требует публиковать и natural, и balanced метрики и мониторить `other_share` в production.

## 8. Известная проблема

Отрицание и конкурирующие признаки. Исторический пример: «Подписку отменять не хочу, нужен чек об оплате» → `subscription`, ожидается `payment`. Английский аналог для нового test: «I don't want to cancel my subscription, I need a receipt» → ожидается `payment`.

Причина: TF-IDF переоценивает слово «subscription/cancel», не понимает отрицание. Нужно:

1. Воспроизвести тестом.
2. Добавить примеры с отрицаниями в train.
3. Проверить char n-grams / transformer / постобработку.
4. Если не исправлено — routing в manual и честное ограничение.

## 9. Воспроизводимость

```bash
python scripts/download_data.py --config configs/data.yaml
python scripts/build_dataset.py --config configs/data.yaml
python scripts/validate_data.py --config configs/data.yaml
python scripts/train.py --config configs/baseline.yaml --allow-provisional
python scripts/make_balanced_test.py
python scripts/evaluate.py --split test
python scripts/evaluate.py --split test --balanced --data data/processed/test_balanced.csv
```

После появления human-verified test убрать `--allow-provisional`: обучение должно падать, если eval содержит слабые метки.

## 10. Что не делаем

- не сравниваемся с коммерческими моделями;
- не обучаем LLM с нуля;
- не используем test для early stopping;
- не выдаём синтетические 0.929 за финальный результат;
- не скрываем падение качества на реальных данных.
