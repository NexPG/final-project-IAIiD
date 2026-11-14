"""CLI: train the TF-IDF + logistic regression baseline."""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from music_support_triage.core.config import load_yaml, resolve_path
from music_support_triage.data.schema import LABELS
from music_support_triage.models.baseline import (
    evaluate,
    save_model,
    train_baseline,
    write_metrics,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("configs/baseline.yaml"))
    parser.add_argument("--data", type=Path, default=None)
    parser.add_argument("--allow-provisional", action="store_true")
    parser.add_argument("--no-save", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = load_yaml(args.config)
    data_path = args.data or resolve_path(config["data_path"])
    frame = pd.read_csv(data_path)

    train = frame[frame["split"] == "train"]
    validation = frame[frame["split"] == "validation"]
    test = frame[frame["split"] == "test"]
    if train.empty or validation.empty or test.empty:
        raise SystemExit("Train, validation and test splits are required")

    weak_test = int((test["label_quality"] != "human_verified").sum())
    allow_provisional = args.allow_provisional or bool(config.get("allow_provisional", False))
    if weak_test and not allow_provisional:
        raise SystemExit(
            "Test split contains weak labels. Pass --allow-provisional for a dev run."
        )

    pipeline, metadata = train_baseline(train, config)
    model_version = f"tfidf-logreg-{datetime.now(UTC):%Y%m%d%H%M%S}"
    metadata["model_version"] = model_version
    metadata["dataset_path"] = str(data_path)
    metadata["provisional"] = bool(weak_test)

    metrics: dict[str, object] = {
        "model_version": model_version,
        "trained_at": metadata["trained_at"],
        "provisional": bool(weak_test),
        "n_train": int(len(train)),
        "n_validation": int(len(validation)),
        "n_test": int(len(test)),
        "validation": evaluate(validation["label"], pipeline.predict(validation["text"])),
        "test": evaluate(test["label"], pipeline.predict(test["text"])),
        "class_support": {label: int((train["label"] == label).sum()) for label in LABELS},
    }

    if not args.no_save:
        save_model(pipeline, metadata, resolve_path(config["model_path"]))
        write_metrics(metrics, resolve_path(config["metrics_path"]))
        write_model_card(metrics, resolve_path(config["model_card_path"]), metadata)

    print(json.dumps(metrics, indent=2, ensure_ascii=False))
    return 0


def write_model_card(metrics: dict[str, object], path: Path, metadata: dict[str, object]) -> None:
    """Write a short model card next to the artifact."""
    test = metrics["test"]
    assert isinstance(test, dict)
    lines = [
        "# Model card: TF-IDF + Logistic Regression",
        "",
        f"- Version: `{metrics['model_version']}`",
        f"- Trained at: {metrics['trained_at']}",
        f"- Train rows: {metrics['n_train']}",
        f"- Validation rows: {metrics['n_validation']}",
        f"- Test rows: {metrics['n_test']}",
        f"- Provisional (weak test labels): {metrics['provisional']}",
        f"- Macro-F1 (validation): {metrics['validation']['macro_f1']:.4f}",  # type: ignore[index]
        f"- Macro-F1 (test): {test['macro_f1']:.4f}",
        "",
        "## Intended use",
        "",
        "Educational prototype for routing music-streaming support tickets.",
        "Not a production decision system; low-confidence requests go to manual review.",
        "",
        "## Limitations",
        "",
        "- Weak labels in TWCS/Bitext training data.",
        "- Test metrics are provisional until human-verified labels exist.",
        "- Rare classes (`content`, `recommendations`) are underrepresented.",
        "",
        "## Training parameters",
        "",
        f"```json\n{json.dumps(metadata.get('params', {}), indent=2)}\n```",
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
