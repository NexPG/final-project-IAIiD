"""CLI: create a class-balanced stress subset from the test split."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from music_support_triage.data.schema import LABELS


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data/processed/dataset.csv"))
    parser.add_argument("--output", type=Path, default=Path("data/processed/test_balanced.csv"))
    parser.add_argument("--min-per-class", type=int, default=25)
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    frame = pd.read_csv(args.data)
    test = frame[frame["split"] == "test"]
    parts = [
        group.sample(min(len(group), args.min_per_class), random_state=args.seed)
        for _, group in test.groupby("label", sort=False)
    ]
    balanced = pd.concat(parts).sort_values(["label", "id"]).reset_index(drop=True)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    balanced.to_csv(args.output, index=False)
    summary = {
        "rows": int(len(balanced)),
        "support": {label: int((balanced["label"] == label).sum()) for label in LABELS},
        "label_quality": {
            str(key): int(value) for key, value in balanced["label_quality"].value_counts().items()
        },
    }
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
