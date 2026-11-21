"""Train the final fixed model without hyperparameter search.

The model family and parameters were selected during the experiments:
TF-IDF word (1,2), min_df=2, max_features=50000, sublinear_tf=False,
LogisticRegression C=32, class_weight=balanced, seed 42.

This script is intentionally deterministic: it trains the known best candidate
on the processed dataset, evaluates it once on test and writes the artifact.
"""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import f1_score

from music_support_triage.core.config import load_yaml
from music_support_triage.data.schema import LABELS
from music_support_triage.models.baseline import (
    build_pipeline,
    evaluate,
    predict_proba,
    save_model,
    write_metrics,
)
from music_support_triage.services.routing import route


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data/processed/dataset.csv"))
    parser.add_argument("--config", type=Path, default=Path("configs/baseline.yaml"))
    parser.add_argument("--service-config", type=Path, default=Path("configs/service.yaml"))
    parser.add_argument("--manifest", type=Path, default=Path("data/manifest.json"))
    parser.add_argument("--output", type=Path, default=Path("artifacts/model.joblib"))
    parser.add_argument("--metrics", type=Path, default=Path("artifacts/metrics_final.json"))
    return parser.parse_args()


def bootstrap_macro_f1(
    y_true: np.ndarray, y_pred: np.ndarray, seed: int = 42, rounds: int = 1000
) -> dict[str, float]:
    rng = np.random.default_rng(seed)
    scores: list[float] = []
    n = len(y_true)
    for _ in range(rounds):
        idx = rng.integers(0, n, n)
        scores.append(
            float(
                f1_score(
                    y_true[idx],
                    y_pred[idx],
                    labels=list(LABELS),
                    average="macro",
                    zero_division=0,
                )
            )
        )
    return {
        "mean": float(np.mean(scores)),
        "ci_low": float(np.quantile(scores, 0.025)),
        "ci_high": float(np.quantile(scores, 0.975)),
    }


def routing_metrics(
    probabilities: np.ndarray, y_true: pd.Series, threshold: float, margin: float
) -> dict[str, float]:
    automatic = 0
    correct = 0
    for row, truth in zip(probabilities, y_true, strict=True):
        decision = route(row, LABELS, threshold=threshold, margin_threshold=margin)
        if not decision.needs_human_review:
            automatic += 1
            correct += int(decision.label == truth)
    total = len(y_true)
    return {
        "coverage": round(automatic / total, 4) if total else 0.0,
        "review_rate": round(1.0 - automatic / total, 4) if total else 0.0,
        "selective_precision": round(correct / automatic, 4) if automatic else 0.0,
    }


def main() -> int:
    args = parse_args()
    config = load_yaml(args.config)
    service_config = load_yaml(args.service_config) if args.service_config.exists() else {}
    frame = pd.read_csv(args.data)
    train = frame[frame["split"] == "train"].reset_index(drop=True)
    test = frame[frame["split"] == "test"].reset_index(drop=True)
    if train.empty or test.empty:
        raise SystemExit("Train and test splits are required")

    params = config.get("model", {})
    pipeline = build_pipeline(
        word_max_features=int(params.get("word_max_features", 50_000)),
        char_max_features=int(params.get("char_max_features", 30_000)),
        c_value=float(params.get("c_value", 32.0)),
        seed=int(config.get("seed", 42)),
        use_char=bool(params.get("use_char", False)),
        word_ngram=tuple(params.get("word_ngram", (1, 2))),
        word_min_df=int(params.get("word_min_df", 2)),
        char_ngram=tuple(params.get("char_ngram", (3, 5))),
        char_min_df=int(params.get("char_min_df", 3)),
        sublinear_tf=bool(params.get("sublinear_tf", False)),
    )
    pipeline.fit(train["text"], train["label"])

    predictions = pipeline.predict(test["text"])
    probabilities = predict_proba(pipeline, test["text"].tolist())
    metrics = evaluate(test["label"], predictions)
    threshold = float(service_config.get("threshold", config.get("threshold", 0.70)))
    margin = float(
        service_config.get("margin_threshold", config.get("margin_threshold", 0.05))
    )
    routing = routing_metrics(probabilities, test["label"], threshold, margin)
    bootstrap = bootstrap_macro_f1(test["label"].to_numpy(), np.asarray(predictions))

    dataset_version = None
    if args.manifest.exists():
        dataset_version = json.loads(args.manifest.read_text(encoding="utf-8")).get(
            "dataset_version"
        )
    model_version = f"final-logreg_word-{datetime.now(UTC):%Y%m%d%H%M%S}"
    metadata = {
        "model_type": "logreg_word",
        "model_version": model_version,
        "trained_at": datetime.now(UTC).isoformat(),
        "n_train": int(len(train)),
        "n_test": int(len(test)),
        "labels": list(LABELS),
        "best_params": {
            "word_max_features": int(params.get("word_max_features", 50_000)),
            "min_df": int(params.get("word_min_df", 2)),
            "ngram_range": list(params.get("word_ngram", (1, 2))),
            "sublinear_tf": bool(params.get("sublinear_tf", False)),
            "C": float(params.get("c_value", 32.0)),
            "class_weight": "balanced",
        },
        "threshold": threshold,
        "margin_threshold": margin,
        "dataset_version": dataset_version,
        "provisional": bool((test["label_quality"] != "human_verified").any()),
    }
    save_model(pipeline, metadata, args.output)
    write_metrics(
        {
            "model_version": model_version,
            "test": metrics,
            "test_routing": routing,
            "bootstrap_macro_f1": bootstrap,
            "threshold": threshold,
            "margin_threshold": margin,
            "dataset_version": dataset_version,
        },
        args.metrics,
    )
    print(
        json.dumps(
            {
                "model_version": model_version,
                "output": str(args.output),
                "accuracy": metrics["accuracy"],
                "macro_f1": metrics["macro_f1"],
                "test_routing": routing,
                "bootstrap_macro_f1": bootstrap,
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
