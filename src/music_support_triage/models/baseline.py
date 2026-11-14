"""TF-IDF + logistic regression baseline and evaluation helpers."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
)
from sklearn.pipeline import FeatureUnion, Pipeline

from music_support_triage.data.schema import LABELS


def build_pipeline(
    word_max_features: int = 50_000,
    char_max_features: int = 50_000,
    c_value: float = 4.0,
    seed: int = 42,
    use_char: bool = True,
    word_ngram: tuple[int, int] = (1, 2),
    word_min_df: int = 2,
    char_ngram: tuple[int, int] = (3, 5),
    char_min_df: int = 2,
) -> Pipeline:
    """Create the reproducible TF-IDF baseline (word, optionally + char)."""
    transformers: list[tuple[str, TfidfVectorizer]] = [
        (
            "word",
            TfidfVectorizer(
                analyzer="word",
                ngram_range=word_ngram,
                min_df=word_min_df,
                max_features=word_max_features,
                sublinear_tf=True,
            ),
        )
    ]
    if use_char:
        transformers.append(
            (
                "char",
                TfidfVectorizer(
                    analyzer="char_wb",
                    ngram_range=char_ngram,
                    min_df=char_min_df,
                    max_features=char_max_features,
                    sublinear_tf=True,
                ),
            )
        )
    features = FeatureUnion(transformers)
    classifier = LogisticRegression(
        C=c_value,
        max_iter=2_000,
        class_weight="balanced",
        random_state=seed,
    )
    return Pipeline([("features", features), ("classifier", classifier)])


def evaluate(y_true: pd.Series, y_pred: np.ndarray, labels: tuple[str, ...] = LABELS) -> dict[str, Any]:
    """Compute the metrics required by the project."""
    present = [label for label in labels if label in set(y_true) or label in set(y_pred)]
    report = classification_report(
        y_true, y_pred, labels=list(labels), output_dict=True, zero_division=0
    )
    matrix = confusion_matrix(y_true, y_pred, labels=list(labels))
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "macro_f1": float(f1_score(y_true, y_pred, labels=list(labels), average="macro", zero_division=0)),
        "weighted_f1": float(f1_score(y_true, y_pred, labels=list(labels), average="weighted", zero_division=0)),
        "per_class": {
            label: {
                "precision": float(report[label]["precision"]),
                "recall": float(report[label]["recall"]),
                "f1": float(report[label]["f1-score"]),
                "support": int(report[label]["support"]),
            }
            for label in labels
            if label in report
        },
        "confusion_matrix": matrix.tolist(),
        "labels": list(labels),
        "present_labels": present,
    }


def train_baseline(
    train_frame: pd.DataFrame,
    config: dict[str, Any],
) -> tuple[Pipeline, dict[str, Any]]:
    """Train the baseline and return the fitted pipeline plus metadata."""
    params = config.get("model", {})
    pipeline = build_pipeline(
        word_max_features=int(params.get("word_max_features", 50_000)),
        char_max_features=int(params.get("char_max_features", 50_000)),
        c_value=float(params.get("c_value", 4.0)),
        seed=int(config.get("seed", 42)),
        use_char=bool(params.get("use_char", True)),
        word_ngram=tuple(params.get("word_ngram", (1, 2))),
        word_min_df=int(params.get("word_min_df", 2)),
        char_ngram=tuple(params.get("char_ngram", (3, 5))),
        char_min_df=int(params.get("char_min_df", 2)),
    )
    pipeline.fit(train_frame["text"], train_frame["label"])
    use_char = bool(params.get("use_char", True))
    metadata = {
        "model_type": "tfidf_word_char_logreg" if use_char else "tfidf_word_logreg",
        "trained_at": datetime.now(UTC).isoformat(),
        "n_train": int(len(train_frame)),
        "labels": list(LABELS),
        "params": {
            "word_max_features": int(params.get("word_max_features", 50_000)),
            "char_max_features": int(params.get("char_max_features", 50_000)),
            "c_value": float(params.get("c_value", 4.0)),
            "use_char": use_char,
            "class_weight": "balanced",
        },
    }
    return pipeline, metadata


def save_model(pipeline: Pipeline, metadata: dict[str, Any], path: Path) -> None:
    """Persist the fitted pipeline and metadata."""
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({"pipeline": pipeline, "metadata": metadata}, path)


def load_model(path: Path) -> tuple[Pipeline, dict[str, Any]]:
    """Load a persisted model bundle."""
    bundle = joblib.load(path)
    if not isinstance(bundle, dict) or "pipeline" not in bundle:
        raise ValueError(f"Invalid model bundle: {path}")
    return bundle["pipeline"], bundle.get("metadata", {})


def predict_proba(pipeline: Pipeline, texts: list[str]) -> np.ndarray:
    """Return class probabilities in the project's fixed label order."""
    probabilities = pipeline.predict_proba(texts)
    classes = list(pipeline.classes_)
    order = [classes.index(label) for label in LABELS]
    return probabilities[:, order]


def write_metrics(metrics: dict[str, Any], path: Path) -> None:
    """Write metrics as JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(metrics, indent=2, ensure_ascii=False), encoding="utf-8")
