"""CLI: routing coverage and selective precision for a fixed threshold."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from music_support_triage.data.schema import LABELS
from music_support_triage.models.baseline import load_model, predict_proba
from music_support_triage.services.routing import route


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", type=Path, default=Path("artifacts/model.joblib"))
    parser.add_argument("--data", type=Path, default=Path("data/processed/dataset.csv"))
    parser.add_argument("--split", choices=["train", "test"], default="test")
    parser.add_argument("--threshold", type=float, default=0.70)
    parser.add_argument("--margin", type=float, default=0.05)
    parser.add_argument("--output", type=Path, default=Path("artifacts/routing_report.json"))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    frame = pd.read_csv(args.data)
    split = frame[frame["split"] == args.split].reset_index(drop=True)
    if split.empty:
        raise SystemExit(f"No rows for split={args.split!r} in {args.data}")
    pipeline, metadata = load_model(args.model)
    probabilities = predict_proba(pipeline, split["text"].tolist())

    auto = 0
    correct = 0
    for row, truth in zip(probabilities, split["label"], strict=True):
        decision = route(row, LABELS, threshold=args.threshold, margin_threshold=args.margin)
        if not decision.needs_human_review:
            auto += 1
            correct += int(decision.label == truth)

    total = len(split)
    report = {
        "model_version": metadata.get("model_version", "unknown"),
        "split": args.split,
        "threshold": args.threshold,
        "margin_threshold": args.margin,
        "rows": total,
        "auto_routed": auto,
        "coverage": round(auto / total, 4),
        "review_rate": round(1.0 - auto / total, 4),
        "selective_precision": round(correct / auto, 4) if auto else 0.0,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
