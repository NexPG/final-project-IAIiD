"""CLI: tune confidence/margin thresholds and report calibration."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from music_support_triage.core.config import load_yaml, resolve_path
from music_support_triage.data.schema import LABELS
from music_support_triage.models.baseline import load_model, predict_proba
from music_support_triage.services.routing import route


def expected_calibration_error(
    confidences: np.ndarray, correct: np.ndarray, bins: int = 10
) -> float:
    """Compute a simple binned ECE for top-1 confidence."""
    edges = np.linspace(0.0, 1.0, bins + 1)
    total = len(confidences)
    if total == 0:
        return 0.0
    error = 0.0
    for low, high in zip(edges[:-1], edges[1:], strict=True):
        mask = (confidences >= low) & (confidences < high)
        count = int(mask.sum())
        if count == 0:
            continue
        accuracy = float(correct[mask].mean())
        confidence = float(confidences[mask].mean())
        error += (count / total) * abs(accuracy - confidence)
    return float(error)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("configs/baseline.yaml"))
    parser.add_argument("--split", choices=["validation", "test"], default="validation")
    parser.add_argument("--output", type=Path, default=Path("artifacts/threshold_tuning.json"))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = load_yaml(args.config)
    data_path = resolve_path(config["data_path"])
    model_path = resolve_path(config["model_path"])
    assert data_path is not None and model_path is not None

    frame = pd.read_csv(data_path)
    subset = frame[frame["split"] == args.split]
    if subset.empty:
        raise SystemExit(f"Split {args.split} is empty")

    pipeline, metadata = load_model(model_path)
    probabilities = predict_proba(pipeline, subset["text"].tolist())
    labels = subset["label"].tolist()
    top_indices = probabilities.argmax(axis=1)
    confidences = probabilities.max(axis=1)
    predicted = [LABELS[index] for index in top_indices]
    correct = np.array([pred == true for pred, true in zip(predicted, labels, strict=True)])

    results = []
    for threshold in [round(value, 2) for value in np.arange(0.3, 1.0, 0.05)]:
        for margin_threshold in [0.0, 0.05, 0.1, 0.15, 0.2]:
            decisions = [
                route(row, LABELS, threshold, margin_threshold) for row in probabilities
            ]
            auto = [decision for decision in decisions if not decision.needs_human_review]
            if auto:
                auto_correct = sum(
                    1
                    for decision, true in zip(decisions, labels, strict=True)
                    if not decision.needs_human_review and decision.label == true
                )
                selective_precision = auto_correct / len(auto)
            else:
                selective_precision = 0.0
            results.append(
                {
                    "threshold": threshold,
                    "margin_threshold": margin_threshold,
                    "coverage": round(len(auto) / len(decisions), 4),
                    "review_rate": round(1 - len(auto) / len(decisions), 4),
                    "selective_precision": round(selective_precision, 4),
                }
            )

    feasible = [item for item in results if item["selective_precision"] >= 0.95]
    best = max(feasible, key=lambda item: item["coverage"]) if feasible else max(
        results, key=lambda item: item["selective_precision"]
    )

    payload = {
        "model_version": metadata.get("model_version", "unknown"),
        "split": args.split,
        "n_rows": int(len(subset)),
        "label_quality": {
            str(key): int(value) for key, value in subset["label_quality"].value_counts().items()
        },
        "ece": round(expected_calibration_error(confidences, correct), 4),
        "accuracy_at_top1": round(float(correct.mean()), 4),
        "best": best,
        "grid": results,
        "note": "Provisional while the split uses weak labels.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({key: payload[key] for key in ("model_version", "split", "ece", "best")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
