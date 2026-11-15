"""CLI: evaluate a saved model on validation or test."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from music_support_triage.core.config import load_yaml, resolve_path
from music_support_triage.data.schema import LABELS
from music_support_triage.models.baseline import evaluate, load_model, write_metrics


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("configs/baseline.yaml"))
    parser.add_argument("--model", type=Path, default=None)
    parser.add_argument("--data", type=Path, default=None)
    parser.add_argument("--split", choices=["validation", "test"], default="test")
    parser.add_argument("--balanced", action="store_true")
    parser.add_argument("--min-per-class", type=int, default=25)
    parser.add_argument("--output", type=Path, default=None)
    return parser.parse_args()


def balanced_subset(frame: pd.DataFrame, min_per_class: int, seed: int = 42) -> pd.DataFrame:
    """Sample up to N rows per class, keeping all rows for scarce classes."""
    parts = [
        group.sample(min(len(group), min_per_class), random_state=seed)
        for _, group in frame.groupby("label", sort=False)
    ]
    return pd.concat(parts).sort_values(["label", "id"]).reset_index(drop=True)


def main() -> int:
    args = parse_args()
    config = load_yaml(args.config)
    data_path = args.data or resolve_path(config["data_path"])
    model_path = args.model or resolve_path(config["model_path"])
    assert data_path is not None and model_path is not None

    frame = pd.read_csv(data_path)
    subset = frame[frame["split"] == args.split].copy()
    if subset.empty:
        raise SystemExit(f"Split {args.split!r} is empty")
    if args.balanced:
        subset = balanced_subset(subset, args.min_per_class)

    pipeline, metadata = load_model(model_path)
    metrics = evaluate(subset["label"], pipeline.predict(subset["text"]))
    result = {
        "model_version": metadata.get("model_version", "unknown"),
        "split": args.split,
        "balanced": args.balanced,
        "n_rows": int(len(subset)),
        "label_quality": {
            str(key): int(value) for key, value in subset["label_quality"].value_counts().items()
        },
        "support": {label: int((subset["label"] == label).sum()) for label in LABELS},
        **metrics,
    }
    output = args.output or Path(f"artifacts/evaluation_{args.split}"
                                 f"{'_balanced' if args.balanced else ''}.json")
    write_metrics(result, output)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
