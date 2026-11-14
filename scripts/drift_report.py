"""CLI: offline data-drift report (PSI + KS) for text length and vocabulary."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import ks_2samp

from music_support_triage.data.text import normalize_for_dedup


def population_stability_index(
    reference: np.ndarray, current: np.ndarray, bins: int = 10
) -> float:
    """Compute PSI over quantile bins of the reference sample."""
    if len(reference) == 0 or len(current) == 0:
        return 0.0
    edges = np.unique(np.quantile(reference, np.linspace(0, 1, bins + 1)))
    if len(edges) < 3:
        return 0.0
    reference_counts, _ = np.histogram(reference, bins=edges)
    current_counts, _ = np.histogram(current, bins=edges)
    reference_share = np.clip(reference_counts / max(reference_counts.sum(), 1), 1e-6, None)
    current_share = np.clip(current_counts / max(current_counts.sum(), 1), 1e-6, None)
    return float(np.sum((current_share - reference_share) * np.log(current_share / reference_share)))


def describe(frame: pd.DataFrame, name: str) -> dict[str, object]:
    text = frame["text"].astype(str)
    lengths = text.str.len().to_numpy()
    tokens = set()
    for value in text.map(normalize_for_dedup):
        tokens.update(value.split())
    return {
        "name": name,
        "rows": int(len(frame)),
        "length_mean": float(lengths.mean()) if len(lengths) else 0.0,
        "length_p95": float(np.percentile(lengths, 95)) if len(lengths) else 0.0,
        "vocabulary_size": len(tokens),
        "other_share": float((frame["label"] == "other").mean()) if "label" in frame else None,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data/processed/dataset.csv"))
    parser.add_argument("--reference-split", default="train")
    parser.add_argument("--current-split", default="test")
    parser.add_argument("--output", type=Path, default=Path("artifacts/drift_report.json"))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    frame = pd.read_csv(args.data)
    reference = frame[frame["split"] == args.reference_split]
    current = frame[frame["split"] == args.current_split]
    if reference.empty or current.empty:
        raise SystemExit("Reference or current split is empty")

    reference_lengths = reference["text"].astype(str).str.len().to_numpy()
    current_lengths = current["text"].astype(str).str.len().to_numpy()
    psi = population_stability_index(reference_lengths, current_lengths)
    ks = ks_2samp(reference_lengths, current_lengths)

    report = {
        "reference": describe(reference, args.reference_split),
        "current": describe(current, args.current_split),
        "length_psi": round(psi, 4),
        "length_ks_statistic": round(float(ks.statistic), 4),
        "length_ks_pvalue": round(float(ks.pvalue), 6),
        "signals": {
            "psi_gt_0_2": psi > 0.2,
            "ks_pvalue_lt_0_05": float(ks.pvalue) < 0.05,
        },
        "note": "Offline demonstration on train vs test; production drift needs real request logs.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
