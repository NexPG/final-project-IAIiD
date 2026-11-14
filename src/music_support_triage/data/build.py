"""Build one combined dataset with an 80/20 stratified train/test split."""

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
QUALITY_PRIORITY = {"human_verified": 0, "weak": 1, "synthetic": 2}


def sha256_file(path: Path) -> str:
    """Return a hex SHA-256 digest for a file."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def deduplicate_combined(frame: pd.DataFrame) -> pd.DataFrame:
    """Drop exact normalized duplicates before splitting, preferring trusted sources."""
    if frame.empty:
        return frame
    result = frame.copy()
    result["_dedup_key"] = result["text"].map(normalize_for_dedup)
    result["_source_priority"] = result["source"].map(SOURCE_PRIORITY).fillna(9)
    result["_quality_priority"] = result["label_quality"].map(QUALITY_PRIORITY).fillna(9)
    result = result.sort_values(["_quality_priority", "_source_priority", "id"])
    result = result.drop_duplicates(subset=["_dedup_key"], keep="first")
    return result.drop(columns=["_dedup_key", "_source_priority", "_quality_priority"])


def assign_stratified_split(
    frame: pd.DataFrame,
    test_fraction: float,
    seed: int,
) -> pd.DataFrame:
    """Split 80/20 stratified by ``(source, label)`` and grouped by conversation."""
    if frame.empty:
        return frame

    result = frame.copy()
    result["stratum"] = result["source"].astype(str) + "||" + result["label"].astype(str)
    assignment: dict[str, str] = {}
    strata = sorted(result["stratum"].unique())

    for index, stratum in enumerate(strata):
        subset = result[result["stratum"] == stratum]
        conversations = sorted(subset["conversation_id"].astype(str).unique())
        shuffled = (
            pd.Series(conversations)
            .sample(frac=1.0, random_state=seed + index)
            .tolist()
        )
        count = len(shuffled)
        n_test = 0
        if count >= 2:
            n_test = max(1, round(count * test_fraction))
            n_test = min(count - 1, n_test)
        for position, conversation_id in enumerate(shuffled):
            assignment[conversation_id] = "test" if position < n_test else "train"

    result["split"] = result["conversation_id"].astype(str).map(assignment)
    result["split"] = result["split"].fillna("train")
    return result


def summarize(frame: pd.DataFrame) -> dict[str, Any]:
    """Return counts used in the dataset manifest."""
    by_split = {split: int((frame["split"] == split).sum()) for split in SPLITS}
    by_source = {str(key): int(value) for key, value in frame["source"].value_counts().items()}
    by_label = {str(key): int(value) for key, value in frame["label"].value_counts().items()}
    by_quality = {
        str(key): int(value) for key, value in frame["label_quality"].value_counts().items()
    }
    by_source_split = {
        f"{source}||{split}": int(
            ((frame["source"] == source) & (frame["split"] == split)).sum()
        )
        for source in sorted(frame["source"].unique())
        for split in SPLITS
    }
    return {
        "rows": int(len(frame)),
        "by_split": by_split,
        "by_source": by_source,
        "by_label": by_label,
        "by_label_quality": by_quality,
        "by_source_split": by_source_split,
    }


def build_dataset(config: dict[str, Any]) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Build the combined dataset and its manifest."""
    paths = config["paths"]
    sampling = config["sampling"]
    split_config = config["splits"]
    seed = int(config.get("seed", 42))

    parts: list[pd.DataFrame] = [
        load_twcs(paths["twcs_dev"], paths["twcs_pseudo"]),
    ]

    bitext_path = paths.get("bitext")
    if bitext_path is not None:
        parts.append(load_bitext(bitext_path, int(sampling["bitext_max_rows"]), seed))

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
    frame = deduplicate_combined(frame)
    frame = assign_stratified_split(
        frame,
        test_fraction=float(split_config.get("test_fraction", 0.2)),
        seed=seed,
    )

    frame = frame.sort_values(["split", "source", "label", "id"]).reset_index(drop=True)
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
        "config": {"sampling": sampling, "splits": split_config},
        "files": {
            name: {"path": str(path), "sha256": sha256_file(path)}
            for name, path in files.items()
        },
        "summary": frame.attrs["summary"],
    }

    manifest_path = paths["manifest"]
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    return frame, manifest
