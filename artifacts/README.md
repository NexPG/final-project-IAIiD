# Artifacts

`model.joblib` — финальная модель `search-logreg_word-20261114200534`, закоммичена
специально, чтобы сервис и Docker-демо запускались из чистого клона без сырых данных.

Модель не содержит PII: это TF-IDF + LogisticRegression и метаданные обучения.
Сырые TWCS/Bitext и промежуточные датасеты по-прежнему не коммитятся.

Полный список метрик и ограничений — в
[`docs/03_experiments/model_card.md`](../docs/03_experiments/model_card.md).
