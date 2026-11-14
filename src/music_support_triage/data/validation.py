"""Dataset validation with pandas rules and explicit severity levels."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from music_support_triage.data.schema import (
    CHANNELS,
    LABEL_QUALITIES,
    LABELS,
    LOCALES,
    REQUIRED_COLUMNS,
    SOURCES,
    SPLITS,
)
from music_support_triage.data.text import EMAIL_RE, PHONE_RE, URL_RE, normalize_for_dedup

PII_TEXT_RE = (EMAIL_RE, PHONE_RE, URL_RE)


def _issue(code: str, message: str, count: int | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {"code": code, "message": message}
    if count is not None:
        payload["count"] = count
    return payload


def validate_dataset(frame: pd.DataFrame, config: dict[str, Any] | None = None) -> dict[str, Any]:
    """Run dataset checks and return a machine-readable report."""
    errors: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    config = config or {}
    split_config = config.get("splits", {})

    missing = [column for column in REQUIRED_COLUMNS if column not in frame.columns]
    if missing:
        errors.append(_issue("missing_columns", f"Missing columns: {missing}"))
        return {"ok": False, "errors": errors, "warnings": warnings, "summary": {}}

    if frame.empty:
        errors.append(_issue("empty_dataset", "Dataset is empty"))
        return {"ok": False, "errors": errors, "warnings": warnings, "summary": {}}

    for column in ("id", "text", "label", "label_quality", "source", "split"):
        null_count = int(frame[column].isna().sum())
        if null_count:
            errors.append(_issue("null_required", f"{column} has nulls", null_count))

    unknown_labels = sorted(set(frame["label"].dropna()) - set(LABELS))
    if unknown_labels:
        errors.append(_issue("unknown_label", f"Unknown labels: {unknown_labels}"))

    unknown_splits = sorted(set(frame["split"].dropna()) - set(SPLITS))
    if unknown_splits:
        errors.append(_issue("unknown_split", f"Unknown splits: {unknown_splits}"))

    unknown_quality = sorted(set(frame["label_quality"].dropna()) - set(LABEL_QUALITIES))
    if unknown_quality:
        errors.append(_issue("unknown_quality", f"Unknown label_quality: {unknown_quality}"))

    unknown_sources = sorted(set(frame["source"].dropna()) - set(SOURCES))
    if unknown_sources:
        errors.append(_issue("unknown_source", f"Unknown sources: {unknown_sources}"))

    for column, allowed in (("channel", CHANNELS), ("locale", LOCALES)):
        if column in frame.columns:
            unknown = sorted(set(frame[column].dropna()) - set(allowed))
            if unknown:
                warnings.append(_issue(f"unknown_{column}", f"Unknown {column}: {unknown}"))

    duplicate_ids = int(frame["id"].duplicated().sum())
    if duplicate_ids:
        errors.append(_issue("duplicate_ids", "Duplicate ids", duplicate_ids))

    lengths = frame["text"].astype(str).str.len()
    short = int((lengths < 10).sum())
    long = int((lengths > 5000).sum())
    if short:
        errors.append(_issue("text_too_short", "Texts shorter than 10 chars", short))
    if long:
        errors.append(_issue("text_too_long", "Texts longer than 5000 chars", long))

    frame = frame.copy()
    frame["_dedup_key"] = frame["text"].astype(str).map(normalize_for_dedup)
    split_counts = frame.groupby("_dedup_key")["split"].nunique()
    cross_split_duplicates = int((split_counts > 1).sum())
    if cross_split_duplicates:
        errors.append(
            _issue(
                "cross_split_duplicates",
                "Normalized duplicate texts appear in more than one split",
                cross_split_duplicates,
            )
        )

    if "conversation_id" in frame.columns:
        conversation_splits = (
            frame.dropna(subset=["conversation_id"])
            .groupby("conversation_id")["split"]
            .nunique()
        )
        leaks = int((conversation_splits > 1).sum())
        if leaks:
            errors.append(
                _issue("conversation_leak", "Conversations cross splits", leaks)
            )

    train = frame[frame["split"] == "train"]
    evaluation = frame[frame["split"].isin(["validation", "test"])]
    if not train.empty:
        other_share = float((train["label"] == "other").mean())
        max_other = float(config.get("sampling", {}).get("other_max_share", 0.50))
        if other_share > max_other + 0.01:
            warnings.append(
                _issue(
                    "other_share_high",
                    f"Train `other` share is {other_share:.2%} (max {max_other:.0%})",
                )
            )
        synthetic_share = float((train["label_quality"] == "synthetic").mean())
        if synthetic_share > 0.15:
            warnings.append(
                _issue(
                    "synthetic_share_high",
                    f"Train synthetic share is {synthetic_share:.2%} (max 15%)",
                )
            )

    if not evaluation.empty:
        weak_eval = int((evaluation["label_quality"] != "human_verified").sum())
        allow_weak = bool(split_config.get("allow_weak_eval", False))
        if weak_eval and not allow_weak:
            errors.append(
                _issue(
                    "weak_eval",
                    "Validation/test contain non-human-verified labels",
                    weak_eval,
                )
            )
        elif weak_eval:
            warnings.append(
                _issue(
                    "provisional_eval",
                    "Validation/test use weak labels: metrics are provisional only",
                    weak_eval,
                )
            )

    test = frame[frame["split"] == "test"]
    min_test = int(split_config.get("min_test_per_class", 0))
    if min_test and not test.empty:
        counts = test["label"].value_counts()
        low = {label: int(counts.get(label, 0)) for label in LABELS if counts.get(label, 0) < min_test}
        if low:
            warnings.append(
                _issue(
                    "low_test_support",
                    f"Classes below {min_test} test examples: {low}",
                )
            )

    for pattern_name, pattern in zip(("email", "phone", "url"), PII_TEXT_RE, strict=True):
        count = int(frame["text"].astype(str).str.contains(pattern, regex=True).sum())
        if count:
            warnings.append(
                _issue(f"unmasked_{pattern_name}", f"Unmasked {pattern_name} patterns in text", count)
            )

    summary = {
        "rows": int(len(frame)),
        "by_split": {split: int((frame["split"] == split).sum()) for split in SPLITS},
        "by_label": {str(key): int(value) for key, value in frame["label"].value_counts().items()},
        "by_quality": {
            str(key): int(value) for key, value in frame["label_quality"].value_counts().items()
        },
    }

    return {
        "ok": not errors,
        "errors": errors,
        "warnings": warnings,
        "summary": summary,
    }


def write_validation_report(report: dict[str, Any], path: Path) -> None:
    """Write the validation report to JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
