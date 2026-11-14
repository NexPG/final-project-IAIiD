"""CLI: run and log several baseline experiments to MLflow."""

from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path

os.environ.setdefault("MLFLOW_DISABLE_AGENT_HINT", "1")

import mlflow
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

from music_support_triage.core.config import load_yaml, resolve_path
from music_support_triage.data.schema import LABELS
from music_support_triage.models.baseline import build_pipeline, evaluate, save_model
from music_support_triage.services.routing import route

KEYWORDS = {
    "payment": ["charge", "charged", "refund", "receipt", "invoice", "billing", "card", "payment"],
    "subscription": ["subscription", "premium", "plan", "renew", "cancel", "membership"],
    "account": ["log in", "login", "password", "account", "hacked", "email", "profile"],
    "app": ["app", "crash", "player", "playback", "offline", "freeze", "install", "buffering"],
    "recommendations": ["recommend", "suggestion", "playlist", "discover", "mix", "feature"],
    "content": ["album", "song", "track", "catalog", "artist", "available", "licensing"],
    "other": [],
}


class KeywordModel:
    """Tiny interpretable keyword baseline with one-hot probabilities."""

    def __init__(self) -> None:
        self.classes_ = np.array(LABELS)

    def fit(self, texts: object = None, labels: object = None) -> KeywordModel:
        """Keyword baseline has no parameters to learn."""
        return self

    def predict(self, texts: list[str]) -> np.ndarray:
        output = []
        for text in texts:
            lowered = text.lower()
            scores = {
                label: sum(1 for word in words if re.search(rf"\b{re.escape(word)}\b", lowered))
                for label, words in KEYWORDS.items()
                if label != "other"
            }
            best = max(scores, key=scores.get) if any(scores.values()) else "other"
            output.append(best)
        return np.array(output)

    def predict_proba(self, texts: list[str]) -> np.ndarray:
        predictions = self.predict(texts)
        probabilities = np.zeros((len(texts), len(LABELS)))
        for index, label in enumerate(predictions):
            probabilities[index, list(LABELS).index(label)] = 1.0
        return probabilities


def word_pipeline(c_value: float, seed: int) -> Pipeline:
    return Pipeline(
        [
            ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=2, sublinear_tf=True)),
            (
                "clf",
                LogisticRegression(
                    C=c_value, max_iter=2_000, class_weight="balanced", random_state=seed
                ),
            ),
        ]
    )


def char_pipeline(c_value: float, seed: int) -> Pipeline:
    return Pipeline(
        [
            ("tfidf", TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), min_df=2, sublinear_tf=True)),
            (
                "clf",
                LogisticRegression(
                    C=c_value, max_iter=2_000, class_weight="balanced", random_state=seed
                ),
            ),
        ]
    )


def ordered_probabilities(model: object, texts: list[str]) -> np.ndarray:
    """Return probabilities in the fixed project label order."""
    probabilities = model.predict_proba(texts)
    classes = list(model.classes_)
    order = [classes.index(label) for label in LABELS]
    return probabilities[:, order]


def balanced_subset(frame: pd.DataFrame, per_class: int = 25) -> pd.DataFrame:
    parts = [
        group.sample(min(len(group), per_class), random_state=42)
        for _, group in frame.groupby("label", sort=False)
    ]
    return pd.concat(parts).reset_index(drop=True)


def routing_metrics(probabilities: np.ndarray, labels: pd.Series) -> dict[str, float]:
    decisions = [route(row, LABELS, threshold=0.70, margin_threshold=0.10) for row in probabilities]
    auto = [decision for decision in decisions if not decision.needs_human_review]
    correct = sum(
        1
        for decision, true in zip(decisions, labels, strict=True)
        if not decision.needs_human_review and decision.label == true
    )
    return {
        "coverage": len(auto) / len(decisions),
        "review_rate": 1 - len(auto) / len(decisions),
        "selective_precision": correct / len(auto) if auto else 0.0,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("configs/baseline.yaml"))
    parser.add_argument("--output", type=Path, default=Path("artifacts/experiments.json"))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = load_yaml(args.config)
    data_path = resolve_path(config["data_path"])
    assert data_path is not None
    frame = pd.read_csv(data_path)
    train = frame[frame["split"] == "train"]
    validation = frame[frame["split"] == "validation"]
    validation_balanced = balanced_subset(validation)
    test = frame[frame["split"] == "test"]
    seed = int(config.get("seed", 42))

    variants = {
        "E0_keyword": KeywordModel(),
        "E1_word_c1": word_pipeline(1.0, seed),
        "E2_word_c4": word_pipeline(4.0, seed),
        "E3_word_c16": word_pipeline(16.0, seed),
        "E4_char_c4": char_pipeline(4.0, seed),
        "E5_word_char_c4": build_pipeline(c_value=4.0, seed=seed),
    }

    mlflow.set_tracking_uri("sqlite:///mlflow.db")
    mlflow.set_experiment("music_support_triage")
    results = []

    for name, model in variants.items():
        print(f"training {name}")
        model.fit(train["text"], train["label"])
        validation_probabilities = ordered_probabilities(model, validation["text"].tolist())
        validation_metrics = evaluate(validation["label"], model.predict(validation["text"]))
        balanced_metrics = evaluate(
            validation_balanced["label"], model.predict(validation_balanced["text"])
        )
        test_metrics = evaluate(test["label"], model.predict(test["text"]))
        validation_routing = routing_metrics(validation_probabilities, validation["label"])

        with mlflow.start_run(run_name=name):
            mlflow.log_params(
                {
                    "variant": name,
                    "seed": seed,
                    "n_train": len(train),
                    "provisional": True,
                }
            )
            mlflow.log_metrics(
                {
                    "val_macro_f1": validation_metrics["macro_f1"],
                    "val_balanced_macro_f1": balanced_metrics["macro_f1"],
                    "test_macro_f1": test_metrics["macro_f1"],
                    "test_accuracy": test_metrics["accuracy"],
                    "coverage": validation_routing["coverage"],
                    "selective_precision": validation_routing["selective_precision"],
                }
            )
            for label, values in validation_metrics["per_class"].items():
                mlflow.log_metric(f"val_recall_{label}", values["recall"])
            mlflow.log_dict(
                {
                    "validation": validation_metrics,
                    "validation_balanced": balanced_metrics,
                    "test": test_metrics,
                },
                "metrics.json",
            )
            mlflow.set_tags({"stage": "3", "owner": "vladimir", "data": "twcs_bitext"})

        results.append(
            {
                "run": name,
                "val_macro_f1": validation_metrics["macro_f1"],
                "val_balanced_macro_f1": balanced_metrics["macro_f1"],
                "test_macro_f1": test_metrics["macro_f1"],
                "test_accuracy": test_metrics["accuracy"],
                **validation_routing,
            }
        )

    results.sort(key=lambda item: item["val_balanced_macro_f1"], reverse=True)
    best = results[0]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")

    best_name = str(best["run"])
    best_model = variants[best_name]
    metadata = {
        "model_type": best_name,
        "model_version": f"baseline-{best_name}",
        "n_train": int(len(train)),
        "labels": list(LABELS),
        "provisional": True,
    }
    save_model(best_model, metadata, resolve_path(config["model_path"]))
    print(json.dumps(results, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
