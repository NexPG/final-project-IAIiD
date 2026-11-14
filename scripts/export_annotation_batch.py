"""CLI: export a stratified frozen-test sample for two independent annotators."""

from __future__ import annotations

import argparse
import math
from pathlib import Path

import pandas as pd

from music_support_triage.data.schema import LABELS

ANNOTATION_COLUMNS = ["id", "text", "split", "label", "notes"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data/processed/dataset.csv"))
    parser.add_argument("--output-dir", type=Path, default=Path("data/annotation"))
    parser.add_argument("--split", default="test")
    parser.add_argument("--limit", type=int, default=400)
    parser.add_argument("--min-per-class", type=int, default=25)
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def stratified_sample(
    frame: pd.DataFrame,
    limit: int,
    min_per_class: int,
    seed: int,
) -> pd.DataFrame:
    """Sample up to limit rows with a per-class floor and proportional fill."""
    if limit <= 0 or frame.empty:
        return frame.iloc[0:0]

    groups = {label: frame[frame["label"] == label] for label in LABELS}
    counts = {label: len(group) for label, group in groups.items()}
    total = sum(counts.values())
    target: dict[str, int] = {}
    for label, count in counts.items():
        proportional = limit * count / total if total else 0.0
        target[label] = min(count, max(min_per_class, math.floor(proportional)))

    while sum(target.values()) < limit:
        candidates = [label for label in LABELS if target[label] < counts[label]]
        if not candidates:
            break
        label = max(candidates, key=lambda item: counts[item] - target[item])
        target[label] += 1
    while sum(target.values()) > limit:
        candidates = [label for label in LABELS if target[label] > min_per_class]
        if not candidates:
            break
        label = max(candidates, key=lambda item: target[item] - min_per_class)
        target[label] -= 1

    parts = [
        groups[label].sample(n=target[label], random_state=seed)
        for label in LABELS
        if target[label] > 0
    ]
    return pd.concat(parts).sample(frac=1.0, random_state=seed).reset_index(drop=True)


def main() -> int:
    args = parse_args()
    frame = pd.read_csv(args.data)
    frame = frame[frame["split"] == args.split]
    if frame.empty:
        raise SystemExit(f"No {args.split} rows to annotate")

    sample = stratified_sample(frame, args.limit, args.min_per_class, args.seed)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    for annotator in ("a", "b"):
        export = sample[["id", "text", "split"]].copy()
        export["label"] = ""
        export["notes"] = ""
        export["annotator"] = annotator
        path = args.output_dir / f"batch_{args.split}_{annotator}.csv"
        export[ANNOTATION_COLUMNS + ["annotator"]].to_csv(path, index=False)
        print(f"wrote {path} ({len(export)} rows)")

    key = sample[["id", "split", "text", "label"]].rename(columns={"label": "weak_label"})
    key_path = args.output_dir / f"key_{args.split}.csv"
    key.to_csv(key_path, index=False)
    print(f"wrote {key_path} (do not share with annotators)")
    print("class support:", {label: int((sample["label"] == label).sum()) for label in LABELS})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
