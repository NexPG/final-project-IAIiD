"""Stage 3: model selection with StratifiedGroupKFold CV and RandomizedSearchCV.

The test split is frozen and evaluated exactly once, after the best pipeline
and its threshold are fixed on out-of-fold train predictions.
"""

from __future__ import annotations

import argparse
import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

os.environ.setdefault("MLFLOW_DISABLE_AGENT_HINT", "1")

import mlflow
import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score
from sklearn.model_selection import (
    RandomizedSearchCV,
    StratifiedGroupKFold,
    cross_val_predict,
)
from sklearn.naive_bayes import ComplementNB
from sklearn.pipeline import FeatureUnion, Pipeline
from sklearn.svm import LinearSVC

from music_support_triage.core.config import load_yaml, resolve_path
from music_support_triage.data.schema import LABELS
from music_support_triage.models.baseline import evaluate, save_model, write_metrics
from music_support_triage.services.routing import route


def word_pipeline() -> Pipeline:
    return Pipeline(
        [
            ("features", TfidfVectorizer(sublinear_tf=True)),
            (
                "classifier",
                LogisticRegression(max_iter=2_000, random_state=42),
            ),
        ]
    )


def word_char_pipeline() -> Pipeline:
    return Pipeline(
        [
            (
                "features",
                FeatureUnion(
                    [
                        ("word", TfidfVectorizer(sublinear_tf=True)),
                        ("char", TfidfVectorizer(analyzer="char_wb", sublinear_tf=True)),
                    ]
                ),
            ),
            (
                "classifier",
                LogisticRegression(max_iter=2_000, random_state=42),
            ),
        ]
    )


def svc_pipeline() -> Pipeline:
    return Pipeline(
        [
            ("features", TfidfVectorizer(sublinear_tf=True)),
            (
                "classifier",
                CalibratedClassifierCV(
                    estimator=LinearSVC(random_state=42, dual="auto"),
                    cv=3,
                ),
            ),
        ]
    )


def cnb_pipeline() -> Pipeline:
    return Pipeline(
        [
            ("features", TfidfVectorizer(sublinear_tf=True)),
            ("classifier", ComplementNB()),
        ]
    )


def word_space() -> dict[str, list[Any]]:
    return {
        "features__ngram_range": [(1, 1), (1, 2)],
        "features__min_df": [1, 2, 3],
        "features__max_features": [20_000, 50_000, 100_000],
        "features__sublinear_tf": [True, False],
        "classifier__C": [0.5, 1.0, 2.0, 4.0, 8.0, 16.0, 32.0],
        "classifier__class_weight": [None, "balanced"],
    }


def word_char_space() -> dict[str, list[Any]]:
    space = {
        "features__word__ngram_range": [(1, 1), (1, 2)],
        "features__word__min_df": [1, 2, 3],
        "features__word__max_features": [20_000, 50_000, 100_000],
        "features__char__ngram_range": [(2, 5), (3, 5)],
        "features__char__min_df": [2, 3],
        "features__char__max_features": [30_000, 50_000],
        "classifier__C": [0.5, 1.0, 2.0, 4.0, 8.0, 16.0],
        "classifier__class_weight": [None, "balanced"],
    }
    return space


def svc_space() -> dict[str, list[Any]]:
    return {
        "features__ngram_range": [(1, 1), (1, 2)],
        "features__min_df": [1, 2, 3],
        "features__max_features": [20_000, 50_000],
        "features__sublinear_tf": [True, False],
        "classifier__estimator__C": [0.1, 0.5, 1.0, 2.0, 4.0],
        "classifier__estimator__class_weight": [None, "balanced"],
    }


def cnb_space() -> dict[str, list[Any]]:
    return {
        "features__ngram_range": [(1, 1), (1, 2)],
        "features__min_df": [1, 2, 3],
        "features__max_features": [20_000, 50_000],
        "classifier__alpha": [0.1, 0.5, 1.0, 2.0],
        "classifier__fit_prior": [True, False],
    }


def ordered_probabilities(model: Any, texts: list[str]) -> np.ndarray:
    probabilities = model.predict_proba(texts)
    classes = list(model.classes_)
    order = [classes.index(label) for label in LABELS]
    return probabilities[:, order]


def routing_metrics(probabilities: np.ndarray, labels: pd.Series, threshold: float, margin: float) -> dict[str, float]:
    decisions = [route(row, LABELS, threshold, margin) for row in probabilities]
    auto = [decision for decision in decisions if not decision.needs_human_review]
    correct = sum(
        1
        for decision, true in zip(decisions, labels, strict=True)
        if not decision.needs_human_review and decision.label == true
    )
    return {
        "coverage": round(len(auto) / len(decisions), 4),
        "review_rate": round(1 - len(auto) / len(decisions), 4),
        "selective_precision": round(correct / len(auto), 4) if auto else 0.0,
    }


def tune_threshold_oof(
    probabilities: np.ndarray,
    truth: pd.Series,
    target_precision: float = 0.95,
    max_coverage: float = 0.90,
) -> dict[str, float]:
    """Choose a safe threshold/margin on out-of-fold predictions.

    The policy deliberately leaves at least 10% of requests for manual review:
    a high-confidence-only classifier is safer than maximizing raw coverage.
    """
    top1 = probabilities.max(axis=1)
    top2 = np.partition(probabilities, -2, axis=1)[:, -2]
    margin = top1 - top2
    predicted = np.array(LABELS)[probabilities.argmax(axis=1)]
    correct = predicted == truth.to_numpy()

    grid: list[dict[str, float]] = []
    for threshold in np.arange(0.40, 0.91, 0.05):
        for margin_threshold in np.arange(0.05, 0.31, 0.05):
            auto = (top1 >= threshold) & (margin >= margin_threshold)
            count = int(auto.sum())
            coverage = count / len(correct)
            precision = float(correct[auto].mean()) if count else 0.0
            grid.append(
                {
                    "threshold": round(float(threshold), 2),
                    "margin_threshold": round(float(margin_threshold), 2),
                    "coverage": round(coverage, 4),
                    "selective_precision": round(precision, 4),
                }
            )
    feasible = [
        item
        for item in grid
        if item["selective_precision"] >= target_precision
        and item["coverage"] <= max_coverage
    ]
    return max(feasible, key=lambda item: item["coverage"]) if feasible else max(
        grid, key=lambda item: (item["selective_precision"] - abs(item["coverage"] - 0.5))
    )


def bootstrap_macro_f1(
    truth: np.ndarray,
    predicted: np.ndarray,
    n_boot: int = 1_000,
    seed: int = 42,
) -> dict[str, float]:
    rng = np.random.default_rng(seed)
    values = []
    for _ in range(n_boot):
        index = rng.integers(0, len(truth), len(truth))
        values.append(
            f1_score(
                truth[index],
                predicted[index],
                labels=list(LABELS),
                average="macro",
                zero_division=0,
            )
        )
    low, high = np.percentile(values, [2.5, 97.5])
    return {"mean": float(np.mean(values)), "ci_low": float(low), "ci_high": float(high)}


def write_model_card(payload: dict[str, Any], path: Path) -> None:
    """Write a compact card for the selected search result."""
    selected = payload["selected"]
    test = payload["test"]
    ci = payload["bootstrap_macro_f1"]
    lines = [
        "# Model card: selected pipeline",
        "",
        f"- Version: `{payload['model_version']}`",
        f"- Family: `{selected['family']}`",
        f"- CV macro-F1: {selected['cv_macro_f1_mean']:.4f} ± {selected['cv_macro_f1_std']:.4f}",
        f"- Test macro-F1: {test['macro_f1']:.4f}",
        f"- Bootstrap 95% CI: [{ci['ci_low']:.4f}; {ci['ci_high']:.4f}]",
        f"- Threshold / margin: {payload['oof_threshold']['threshold']} / "
        f"{payload['oof_threshold']['margin_threshold']}",
        f"- Test coverage: {payload['test_routing']['coverage']}",
        f"- Test selective precision: {payload['test_routing']['selective_precision']}",
        f"- Provisional: {payload['provisional']}",
        "",
        "## Selected hyperparameters",
        "",
        f"```json\n{json.dumps(selected['best_params'], indent=2)}\n```",
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("configs/data.yaml"))
    parser.add_argument("--n-iter", type=int, default=12)
    parser.add_argument("--cv-folds", type=int, default=5)
    parser.add_argument("--output", type=Path, default=Path("artifacts/search_results.json"))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = load_yaml(args.config)
    paths = config["paths"]
    data_path = resolve_path(paths["processed"]) if "processed" in paths else Path("data/processed/dataset.csv")
    assert data_path is not None

    frame = pd.read_csv(data_path)
    train = frame[frame["split"] == "train"].reset_index(drop=True)
    test = frame[frame["split"] == "test"].reset_index(drop=True)
    if train.empty or test.empty:
        raise SystemExit("Train and test splits are required")

    seed = int(config.get("seed", 42))
    groups = train["conversation_id"].astype(str).to_numpy()
    cv = StratifiedGroupKFold(n_splits=args.cv_folds, shuffle=True, random_state=seed)

    families = {
        "logreg_word": (word_pipeline(), word_space()),
        "logreg_word_char": (word_char_pipeline(), word_char_space()),
        "linear_svc": (svc_pipeline(), svc_space()),
        "complement_nb": (cnb_pipeline(), cnb_space()),
    }

    mlflow.set_tracking_uri("sqlite:///mlflow.db")
    mlflow.set_experiment("music_support_triage")
    search_results: list[dict[str, Any]] = []
    best_searches: dict[str, RandomizedSearchCV] = {}

    for name, (pipeline, space) in families.items():
        print(f"searching {name}")
        search = RandomizedSearchCV(
            estimator=pipeline,
            param_distributions=space,
            n_iter=args.n_iter,
            scoring="f1_macro",
            cv=cv,
            random_state=seed,
            n_jobs=2,
            refit=True,
            error_score="raise",
            verbose=1,
        )
        search.fit(train["text"], train["label"], groups=groups)
        best_searches[name] = search
        record = {
            "family": name,
            "cv_macro_f1_mean": float(search.best_score_),
            "cv_macro_f1_std": float(search.cv_results_["std_test_score"][search.best_index_]),
            "best_params": search.best_params_,
            "n_iter": args.n_iter,
        }
        search_results.append(record)
        with mlflow.start_run(run_name=f"search_{name}"):
            mlflow.log_params(
                {
                    "family": name,
                    "n_iter": args.n_iter,
                    "cv_folds": args.cv_folds,
                    "seed": seed,
                    "n_train": len(train),
                }
            )
            mlflow.log_metrics(
                {
                    "cv_macro_f1_mean": record["cv_macro_f1_mean"],
                    "cv_macro_f1_std": record["cv_macro_f1_std"],
                }
            )
            mlflow.log_dict(record, "search_result.json")

    search_results.sort(key=lambda item: item["cv_macro_f1_mean"], reverse=True)
    best_record = search_results[0]
    best_name = str(best_record["family"])
    best_search = best_searches[best_name]
    best_model = best_search.best_estimator_

    # Out-of-fold probabilities on train only: no test leakage.
    oof_probabilities = cross_val_predict(
        best_model,
        train["text"],
        train["label"],
        groups=groups,
        cv=cv,
        method="predict_proba",
        n_jobs=2,
    )
    class_order = list(best_model.classes_)
    oof_probabilities = oof_probabilities[:, [class_order.index(label) for label in LABELS]]
    threshold = tune_threshold_oof(oof_probabilities, train["label"])

    # Freeze everything before touching test.
    test_probabilities = ordered_probabilities(best_model, test["text"].tolist())
    test_predictions = best_model.predict(test["text"])
    test_metrics = evaluate(test["label"], test_predictions)
    test_routing = routing_metrics(
        test_probabilities,
        test["label"],
        threshold["threshold"],
        threshold["margin_threshold"],
    )
    bootstrap = bootstrap_macro_f1(
        test["label"].to_numpy(),
        np.asarray(test_predictions),
        seed=seed,
    )

    model_version = f"search-{best_name}-{datetime.now(UTC):%Y%m%d%H%M%S}"
    metadata = {
        "model_type": best_name,
        "model_version": model_version,
        "trained_at": datetime.now(UTC).isoformat(),
        "n_train": int(len(train)),
        "n_test": int(len(test)),
        "labels": list(LABELS),
        "best_params": best_record["best_params"],
        "cv_macro_f1_mean": best_record["cv_macro_f1_mean"],
        "cv_macro_f1_std": best_record["cv_macro_f1_std"],
        "threshold": threshold["threshold"],
        "margin_threshold": threshold["margin_threshold"],
        "provisional": bool((test["label_quality"] != "human_verified").any()),
    }
    save_model(best_model, metadata, resolve_path(paths.get("model_path", "artifacts/model.joblib")))

    output = {
        "model_version": model_version,
        "selection_metric": "StratifiedGroupKFold macro-F1 on train",
        "families": search_results,
        "selected": best_record,
        "oof_threshold": threshold,
        "test": test_metrics,
        "test_routing": test_routing,
        "bootstrap_macro_f1": bootstrap,
        "n_train": int(len(train)),
        "n_test": int(len(test)),
        "provisional": metadata["provisional"],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
    write_metrics(output, Path("artifacts/metrics.json"))
    write_model_card(output, Path("artifacts/model_card.md"))

    with mlflow.start_run(run_name=f"final_{best_name}"):
        mlflow.log_metrics(
            {
                "test_macro_f1": test_metrics["macro_f1"],
                "test_accuracy": test_metrics["accuracy"],
                "test_weighted_f1": test_metrics["weighted_f1"],
                "bootstrap_macro_f1_low": bootstrap["ci_low"],
                "bootstrap_macro_f1_high": bootstrap["ci_high"],
                "coverage": test_routing["coverage"],
                "selective_precision": test_routing["selective_precision"],
                "threshold": threshold["threshold"],
                "margin_threshold": threshold["margin_threshold"],
            }
        )
        mlflow.log_dict(output, "final_metrics.json")

    print(json.dumps(output, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
