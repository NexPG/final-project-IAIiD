# Журнал экспериментов

**Статус:** draft, заполняется на этапе 3  
**Источник требований:** [`TZ.md`](TZ.md), §9; вебинары В05–В07

## 1. Правила

1. Test не используется для подбора гиперпараметров.
2. Validation — только human-verified, после расширения.
3. Синтетика не попадает в validation/test.
4. Каждый run логирует params, metrics, artifacts, tags.
5. Фиксируются Git commit, seed, data manifest, версии.
6. Вывод по каждому эксперименту обязателен.

## 2. Текущий baseline (из черновика)

Черновик этапа 3 уже дал 6 MLflow runs на 420 синтетических примерах:

| Запуск | Признаки | C | Macro-F1 val | Macro-F1 test | Accuracy test |
|---|---|---|---|---|---|
| Keyword baseline | keywords | — | 0.748 | 0.837 | 0.833 |
| Words | word | 0.5 | 0.726 | 0.704 | 0.702 |
| Words | word | 4.0 | 0.722 | 0.739 | 0.738 |
| Words | word | 16.0 | 0.735 | 0.750 | 0.750 |
| Words + chars | word_char | 4.0 | 0.917 | 0.929 | 0.929 |
| Words + chars | word_char | 16.0 | 0.904 | 0.929 | 0.929 |

**Важно:** это метрики на синтетическом test из 84 примеров, по 12 на класс. Они не являются финальными и не подтверждены на реальном потоке. Используем их как baseline для повторной проверки.

## 3. Целевые эксперименты

| ID | Гипотеза | Конфигурация | Что сравниваем | Статус |
|---|---|---|---|---|
| E0 | Keyword baseline — нижняя граница | эвристики | macro-F1, latency | Есть |
| E1 | TF-IDF word + LogReg | C=0.5/4/16 | macro-F1, recall | Есть |
| E2 | Char n-grams помогают на опечатках | word+char, C=4/16 | macro-F1, robustness | Есть |
| E3 | LinearSVC/CNB конкурентен | TF-IDF + LinearSVC/CNB | macro-F1, скорость | План |
| E4 | Калибровка + threshold/margin | CalibratedClassifierCV | coverage, selective precision, ECE | План |
| E5 | Transformer лучше на перефразированиях | ruBERT-tiny2 | macro-F1, latency, размер | Опционально |

Минимум: 3 варианта, 5+ MLflow runs. Цель: 6–8 runs на новом human-verified split.

## 4. Метрики

| Метрика | Цель |
|---|---|
| Macro-F1 | ≥ 0.80 |
| Recall каждого класса | ≥ 0.65 |
| Selective precision | ≥ 0.95 |
| Coverage | ≥ 0.40 |
| Review rate | ≤ 0.60 |
| ECE | ≤ 0.10 |
| p95 latency | ≤ 300 мс |

## 5. MLflow

- Experiment: `music_support_triage`.
- Run name: `<model>-<dataset_version>-<seed>`.
- Params: model, C, ngram_range, seed, dataset_version, threshold.
- Metrics: val/test macro-F1, accuracy, per-class recall, coverage, selective precision, ECE, latency.
- Artifacts: model, confusion matrix, classification report, config, data manifest.
- Tags: `code_sha256`, `dataset_sha256`, `owner`, `stage`.

## 6. Error analysis

- confusion matrix;
- top-20 ошибок;
- разбивка по классам, длине, каналу, языку;
- `other` и неоднозначные;
- отрицания;
- опечатки/транслит;
- калибровка;
- вывод и следующий шаг.

## 7. Известная проблема

«Подписку отменять не хочу, нужен чек об оплате» → модель предсказывает `subscription`, ожидается `payment`. Причина: TF-IDF переоценивает слово «подписку», не понимает отрицание. Нужно:

1. Воспроизвести тестом.
2. Добавить примеры с отрицаниями.
3. Проверить char n-grams / transformer / постобработку.
4. Если не исправлено — routing в manual и честное ограничение.

## 8. Воспроизводимость

```bash
python scripts/train.py --config configs/baseline.yaml
python scripts/evaluate.py --run-id <id>
```

Команды уточняются после реализации. README должен позволять повторить лучший run.
