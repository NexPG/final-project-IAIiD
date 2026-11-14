"""Build a reproducible train/validation/test dataset from public sources."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from music_support_triage.data.loaders import (
    load_bitext,
    load_human,
    load_synthetic,
    load_twcs,
)
from music_support_triage.data.schema import LABELS, SPLITS
from music_support_triage.data.text import normalize_for_dedup

SOURCE_PRIORITY = {"human": 0, "weak_twcs": 1, "bitext": 2, "synthetic": 3}
SPLIT_PRIORITY = {"test": 0, "validation": 1, "train": 2}
QUALITY_PRIORITY = {"human_verified": 0, "weak": 1, "synthetic": 2}


def sha256_file(path: Path) -> str:
    """Return a hex SHA-256 digest for a file."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def assign_group_splits(
    frame: pd.DataFrame,
    validation_fraction: float,
    test_fraction: float,
    seed: int,
) -> pd.DataFrame:
    """Assign whole TWCS conversations to splits, stratified by weak label."""
    if frame.empty:
        return frame

    groups = frame.groupby("conversation_id", sort=False)
    group_labels = groups["label"].agg(lambda values: values.mode().iloc[0])
    total = len(group_labels)
    if total == 0:
        return frame

    test_ratio = min(1.0, test_fraction)
    validation_ratio = min(1.0 - test_ratio, validation_fraction)
    assignment: dict[str, str] = {}

    for label in LABELS:
        ids = list(group_labels[group_labels == label].index)
        rng = pd.Series(ids).sample(frac=1.0, random_state=seed).tolist()
        count = len(rng)
        n_test = min(count, round(count * test_ratio))
        n_validation = min(count - n_test, round(count * validation_ratio))
        for index, conversation_id in enumerate(rng):
            if index < n_test:
                assignment[str(conversation_id)] = "test"
            elif index < n_test + n_validation:
                assignment[str(conversation_id)] = "validation"
            else:
                assignment[str(conversation_id)] = "train"

    result = frame.copy()
    result["split"] = result["conversation_id"].astype(str).map(assignment)
    result["split"] = result["split"].fillna("train")
    return result


def cap_other_share(frame: pd.DataFrame, max_share: float, seed: int) -> pd.DataFrame:
    """Downsample `other` so it does not dominate the training pool."""
    if frame.empty or "other" not in set(frame["label"]):
        return frame

    other = frame[frame["label"] == "other"]
    non_other = frame[frame["label"] != "other"]
    if non_other.empty:
        return frame

    target_other = int(len(non_other) * max_share / (1.0 - max_share))
    if len(other) <= target_other:
        return frame
    kept_other = other.sample(n=target_other, random_state=seed)
    return pd.concat([non_other, kept_other], ignore_index=True)


def deduplicate_across_splits(frame: pd.DataFrame) -> pd.DataFrame:
    """Drop exact duplicates, keeping evaluation rows and trusted sources."""
    if frame.empty:
        return frame

    result = frame.copy()
    result["_dedup_key"] = result["text"].map(normalize_for_dedup)
    result["_source_priority"] = result["source"].map(SOURCE_PRIORITY).fillna(9)
    result["_split_priority"] = result["split"].map(SPLIT_PRIORITY).fillna(9)
    result["_quality_priority"] = result["label_quality"].map(QUALITY_PRIORITY).fillna(9)
    result = result.sort_values(
        ["_split_priority", "_quality_priority", "_source_priority", "id"]
    )
    result = result.drop_duplicates(subset=["_dedup_key"], keep="first")
    return result.drop(columns=["_dedup_key", "_source_priority", "_split_priority", "_quality_priority"])


def summarize(frame: pd.DataFrame) -> dict[str, Any]:
    """Return counts used in the dataset manifest."""
    by_split = {split: int((frame["split"] == split).sum()) for split in SPLITS}
    by_source = {str(key): int(value) for key, value in frame["source"].value_counts().items()}
    by_label = {str(key): int(value) for key, value in frame["label"].value_counts().items()}
    by_quality = {
        str(key): int(value) for key, value in frame["label_quality"].value_counts().items()
    }
    return {
        "rows": int(len(frame)),
        "by_split": by_split,
        "by_source": by_source,
        "by_label": by_label,
        "by_label_quality": by_quality,
    }


def build_dataset(config: dict[str, Any]) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Build the dataset and its manifest from the configured sources."""
    paths = config["paths"]
    sampling = config["sampling"]
    split_config = config["splits"]
    seed = int(config.get("seed", 42))

    twcs = load_twcs(paths["twcs_dev"], paths["twcs_pseudo"])
    twcs = assign_group_splits(
        twcs,
        validation_fraction=float(split_config.get("validation_fraction", 0.0)),
        test_fraction=float(split_config.get("test_fraction", 0.2)),
        seed=seed,
    )

    parts: list[pd.DataFrame] = [twcs]

    bitext_path = paths.get("bitext")
    if bitext_path is not None:
        bitext = load_bitext(bitext_path, int(sampling["bitext_max_rows"]), seed)
        parts.append(bitext)

    synthetic_path = paths.get("synthetic")
    if synthetic_path is not None:
        synthetic = load_synthetic(synthetic_path)
        if len(synthetic) > int(sampling["synthetic_max_rows"]):
            synthetic = synthetic.sample(
                n=int(sampling["synthetic_max_rows"]), random_state=seed
            )
        parts.append(synthetic)

    human_path = paths.get("human")
    if human_path is not None:
        parts.append(load_human(human_path))

    frame = pd.concat(parts, ignore_index=True, sort=False)
    frame = frame[frame["label"].isin(LABELS)]

    train_mask = frame["split"] == "train"
    train = cap_other_share(
        frame[train_mask], float(sampling["other_max_share"]), seed
    )
    evaluation = frame[~train_mask]
    frame = pd.concat([train, evaluation], ignore_index=True, sort=False)
    frame = deduplicate_across_splits(frame)

    frame = frame.sort_values(["split", "label", "id"]).reset_index(drop=True)
    frame.attrs["summary"] = summarize(frame)

    output_path = paths["processed"]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(output_path, index=False)

    files = {
        "twcs_dev": paths["twcs_dev"],
        "twcs_pseudo": paths["twcs_pseudo"],
    }
    if bitext_path is not None:
        files["bitext"] = bitext_path
    if synthetic_path is not None:
        files["synthetic"] = synthetic_path
    if human_path is not None:
        files["human"] = human_path

    manifest: dict[str, Any] = {
        "dataset_version": f"sha256:{sha256_file(output_path)}",
        "generated_at": datetime.now(UTC).isoformat(),
        "seed": seed,
        "config": {
            "sampling": sampling,
            "splits": split_config,
        },
        "files": {name: {"path": str(path), "sha256": sha256_file(path)} for name, path in files.items()},
        "summary": frame.attrs["summary"],
    }

    manifest_path = paths["manifest"]
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    return frame, manifest
