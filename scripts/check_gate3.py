"""CLI: verify Gate 3 and compute final human-verified test metrics."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import f1_score

from music_support_triage.core.config import load_yaml, resolve_path
from music_support_triage.data.schema import LABELS
from music_support_triage.data.text import normalize_for_dedup
from music_support_triage.models.baseline import evaluate, load_model, predict_proba
from music_support_triage.services.routing import route

REQUIRED = {"id", "text", "label", "split"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--annotations", type=Path, default=Path("data/processed/human_verified.csv"))
    parser.add_argument("--kappa-report", type=Path, default=Path("data/annotation/kappa_report.json"))
    parser.add_argument("--dataset", type=Path, default=Path("data/processed/dataset.csv"))
    parser.add_argument("--config", type=Path, default=Path("configs/baseline.yaml"))
    parser.add_argument("--output", type=Path, default=Path("artifacts/gate3_metrics.json"))
    parser.add_argument("--min-rows", type=int, default=400)
    parser.add_argument("--min-kappa", type=float, default=0.70)
    return parser.parse_args()


def bootstrap_macro_f1(truth: np.ndarray, predicted: np.ndarray, n_boot: int = 1000, seed: int = 42) -> dict[str, float]:
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


def main() -> int:
    args = parse_args()
    if not args.annotations.exists():
        print("Gate 3 is blocked: no human-verified annotations yet.")
        print(f"Expected file: {args.annotations}")
        print("Next steps:")
        print("  1) Fill label columns in data/annotation/batch_test_a.csv and batch_test_b.csv")
        print("  2) python scripts/merge_annotations.py --a ... --b ...")
        print("  3) Re-run this script")
        return 2

    frame = pd.read_csv(args.annotations)
    missing = REQUIRED - set(frame.columns)
    if missing:
        raise SystemExit(f"Missing columns: {sorted(missing)}")
    frame = frame[frame["label"].isin(LABELS)].drop_duplicates(subset=["id"])
    if len(frame) < args.min_rows:
        raise SystemExit(f"Need at least {args.min_rows} rows, got {len(frame)}")
    if set(frame["split"]) != {"test"}:
        raise SystemExit(f"Annotations must come from test split, got {set(frame['split'])}")

    if not args.kappa_report.exists():
        raise SystemExit("kappa_report.json is missing; run merge_annotations.py first")
    kappa_payload = json.loads(args.kappa_report.read_text(encoding="utf-8"))
    kappa = float(kappa_payload.get("cohen_kappa", 0.0))
    if kappa < args.min_kappa:
        raise SystemExit(f"Cohen's kappa {kappa:.3f} < {args.min_kappa:.2f}")

    dataset = pd.read_csv(args.dataset)
    train = dataset[dataset["split"] == "train"]
    train_ids = set(train["id"].astype(str))
    train_texts = set(train["text"].astype(str).map(normalize_for_dedup))
    train_conversations = set(train["conversation_id"].dropna().astype(str))

    leaked_ids = set(frame["id"].astype(str)) & train_ids
    leaked_texts = set(frame["text"].astype(str).map(normalize_for_dedup)) & train_texts
    leaked_conversations = set(frame.get("conversation_id", pd.Series(dtype=str)).dropna().astype(str)) & train_conversations
    if leaked_ids or leaked_texts or leaked_conversations:
        raise SystemExit(
            "Leakage detected: "
            f"ids={len(leaked_ids)}, texts={len(leaked_texts)}, conversations={len(leaked_conversations)}"
        )

    config = load_yaml(args.config)
    model_path = resolve_path(config["model_path"])
    assert model_path is not None
    pipeline, metadata = load_model(model_path)
    probabilities = predict_proba(pipeline, frame["text"].tolist())
    predicted = pipeline.predict(frame["text"])
    metrics = evaluate(frame["label"], predicted)
    ci = bootstrap_macro_f1(frame["label"].to_numpy(), np.asarray(predicted))

    threshold = float(config.get("threshold", 0.85))
    margin = float(config.get("margin_threshold", 0.05))
    decisions = [route(row, LABELS, threshold, margin) for row in probabilities]
    auto = [decision for decision in decisions if not decision.needs_human_review]
    auto_correct = sum(
        1
        for decision, truth in zip(decisions, frame["label"], strict=True)
        if not decision.needs_human_review and decision.label == truth
    )
    routing = {
        "coverage": round(len(auto) / len(decisions), 4),
        "review_rate": round(1 - len(auto) / len(decisions), 4),
        "selective_precision": round(auto_correct / len(auto), 4) if auto else 0.0,
    }

    result = {
        "gate": "3",
        "status": "passed" if kappa >= args.min_kappa and ci["ci_low"] > 0 else "failed",
        "model_version": metadata.get("model_version", "unknown"),
        "n_test": int(len(frame)),
        "cohen_kappa": kappa,
        "metrics": metrics,
        "bootstrap_macro_f1": ci,
        "routing": routing,
        "label_quality": {
            str(key): int(value) for key, value in frame.get("label_quality", pd.Series()).value_counts().items()
        },
        "support": {label: int((frame["label"] == label).sum()) for label in LABELS},
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
