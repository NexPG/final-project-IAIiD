# Artifacts

`model.joblib` is generated locally by:

```bash
python scripts/train/train_final.py
```

It is not committed: the model is trained from the downloaded TWCS/Bitext data and
the fixed best hyperparameters. Raw data and model artifacts stay out of git.

Full metrics and limitations — in
[`docs/03_experiments/model_card.md`](../docs/03_experiments/model_card.md).
