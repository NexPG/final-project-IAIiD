"""CLI: merge two independent annotations, compute kappa and export labels."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd
from sklearn.metrics import cohen_kappa_score

from music_support_triage.data.schema import LABELS


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--a", type=Path, required=True)
    parser.add_argument("--b", type=Path, required=True)
    parser.add_argument("--adjudicated", type=Path, default=None)
    parser.add_argument("--output", type=Path, default=Path("data/processed/human_verified.csv"))
    parser.add_argument("--disagreements", type=Path, default=Path("data/annotation/disagreements.csv"))
    parser.add_argument("--report", type=Path, default=Path("data/annotation/kappa_report.json"))
    return parser.parse_args()


def read_annotations(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path)
    required = {"id", "text", "split", "label"}
    missing = required - set(frame.columns)
    if missing:
        raise SystemExit(f"{path} missing columns: {sorted(missing)}")
    frame = frame.copy()
    frame["label"] = frame["label"].astype(str).str.strip().str.lower()
    frame = frame[frame["label"].isin(LABELS)]
    frame = frame.drop_duplicates(subset=["id"], keep="first")
    return frame


def main() -> int:
    args = parse_args()
    left = read_annotations(args.a)
    right = read_annotations(args.b)
    joined = left.merge(right, on="id", suffixes=("_a", "_b"), how="inner")
    if joined.empty:
        raise SystemExit("No overlapping ids between annotators")

    kappa = float(cohen_kappa_score(joined["label_a"], joined["label_b"]))
    agreement = float((joined["label_a"] == joined["label_b"]).mean())

    adjudicated: dict[str, str] = {}
    if args.adjudicated is not None and args.adjudicated.exists():
        adj = pd.read_csv(args.adjudicated)
        adj["label"] = adj["label"].astype(str).str.strip().str.lower()
        adjudicated = {
            str(row.id): str(row.label)
            for row in adj.itertuples(index=False)
            if str(row.label) in LABELS
        }

    resolved = []
    disagreements = []
    for row in joined.itertuples(index=False):
        identifier = str(row.id)
        if identifier in adjudicated:
            label = adjudicated[identifier]
        elif row.label_a == row.label_b:
            label = row.label_a
        else:
            disagreements.append(
                {
                    "id": identifier,
                    "text": row.text_a,
                    "split": row.split_a,
                    "label_a": row.label_a,
                    "label_b": row.label_b,
                }
            )
            continue
        resolved.append(
            {
                "id": identifier,
                "text": row.text_a,
                "label": label,
                "split": row.split_a,
                "label_quality": "human_verified",
                "source": "human",
                "conversation_id": identifier,
                "channel": "twitter",
                "locale": "en",
            }
        )

    output = pd.DataFrame(resolved)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    output.to_csv(args.output, index=False)
    args.disagreements.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(disagreements).to_csv(args.disagreements, index=False)

    report = {
        "annotated_overlap": int(len(joined)),
        "resolved": int(len(output)),
        "disagreements": int(len(disagreements)),
        "agreement": round(agreement, 4),
        "cohen_kappa": round(kappa, 4),
        "kappa_ok": kappa >= 0.70,
        "split_counts": {
            str(key): int(value) for key, value in output["split"].value_counts().items()
        },
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if kappa >= 0.70 else 1


if __name__ == "__main__":
    raise SystemExit(main())
