"""CLI: export validation/test rows for independent human annotation."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

ANNOTATION_COLUMNS = ["id", "text", "split", "label", "notes"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data/processed/dataset.csv"))
    parser.add_argument("--output-dir", type=Path, default=Path("data/annotation"))
    parser.add_argument("--split", choices=["validation", "test", "all"], default="all")
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    frame = pd.read_csv(args.data)
    if args.split != "all":
        frame = frame[frame["split"] == args.split]
    else:
        frame = frame[frame["split"].isin(["validation", "test"])]
    if frame.empty:
        raise SystemExit("No evaluation rows to annotate")

    frame = frame.sample(frac=1.0, random_state=args.seed).reset_index(drop=True)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    for annotator in ("a", "b"):
        export = frame[["id", "text", "split"]].copy()
        export["label"] = ""
        export["notes"] = ""
        export["annotator"] = annotator
        path = args.output_dir / f"batch_{args.split}_{annotator}.csv"
        export[ANNOTATION_COLUMNS + ["annotator"]].to_csv(path, index=False)
        print(f"wrote {path} ({len(export)} rows)")

    key = frame[["id", "split", "text", "label"]].rename(columns={"label": "weak_label"})
    key_path = args.output_dir / f"key_{args.split}.csv"
    key.to_csv(key_path, index=False)
    print(f"wrote {key_path} (do not share with annotators)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
