"""Dataset loaders for TWCS, Bitext, synthetic and human-verified data."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from music_support_triage.data.labels import map_bitext, map_twcs_intent
from music_support_triage.data.schema import LABELS
from music_support_triage.data.text import clean_text, is_usable

TWCS_COLUMNS = ("case_id", "customer_text", "conversation_id", "created_at")


def _require_columns(frame: pd.DataFrame, columns: tuple[str, ...], name: str) -> None:
    missing = [column for column in columns if column not in frame.columns]
    if missing:
        raise ValueError(f"{name} is missing columns: {missing}")


def _base_frame(rows: list[dict[str, Any]]) -> pd.DataFrame:
    frame = pd.DataFrame(rows)
    if frame.empty:
        return frame
    frame = frame[frame["text"].map(is_usable)]
    frame = frame.drop_duplicates(subset=["id"]).reset_index(drop=True)
    return frame


def load_twcs(dev_path: Path, pseudo_path: Path) -> pd.DataFrame:
    """Load SpotifyCares dev cases joined with weak intent labels."""
    dev = pd.read_csv(dev_path)
    pseudo = pd.read_csv(pseudo_path)
    _require_columns(dev, TWCS_COLUMNS, "TWCS dev file")
    _require_columns(pseudo, ("case_id", "intent"), "TWCS pseudo-label file")

    merged = dev.merge(
        pseudo[["case_id", "intent", "pseudo_label_method"]],
        on="case_id",
        how="inner",
        validate="one_to_one",
    )

    rows: list[dict[str, Any]] = []
    for row in merged.itertuples(index=False):
        text = clean_text(row.customer_text)
        if not is_usable(text):
            continue
        label = map_twcs_intent(str(row.intent), text)
        rows.append(
            {
                "id": f"twcs-{row.case_id}",
                "text": text,
                "label": label,
                "label_quality": "weak",
                "source": "weak_twcs",
                "split": "train",
                "conversation_id": f"twcs-{row.conversation_id}",
                "channel": "twitter",
                "locale": "en",
                "created_at": str(row.created_at),
                "source_label": str(row.intent),
                "label_method": str(row.pseudo_label_method),
            }
        )
    return _base_frame(rows)


def load_bitext(path: Path, max_rows: int, seed: int) -> pd.DataFrame:
    """Load and map the Bitext customer-support dataset."""
    frame = pd.read_csv(path)
    _require_columns(frame, ("instruction", "category", "intent"), "Bitext file")

    frame = frame.copy()
    frame["text"] = frame["instruction"].map(clean_text)
    frame = frame[frame["text"].map(is_usable)]
    frame["label"] = [
        map_bitext(str(category), str(intent), str(text))
        for category, intent, text in zip(
            frame["category"], frame["intent"], frame["text"], strict=True
        )
    ]
    frame = frame[frame["label"].isin(LABELS)]

    if max_rows > 0 and len(frame) > max_rows:
        per_class = max(1, max_rows // len(LABELS))
        parts = [
            group.sample(min(len(group), per_class), random_state=seed)
            for _, group in frame.groupby("label", sort=False)
        ]
        sampled = pd.concat(parts)
        if len(sampled) < max_rows:
            rest = frame.drop(index=sampled.index, errors="ignore")
            extra = rest.sample(min(len(rest), max_rows - len(sampled)), random_state=seed)
            sampled = pd.concat([sampled, extra])
        frame = sampled.head(max_rows).reset_index(drop=True)

    rows: list[dict[str, Any]] = []
    for index, row in enumerate(frame.itertuples(index=False)):
        rows.append(
            {
                "id": f"bitext-{index}",
                "text": row.text,
                "label": row.label,
                "label_quality": "weak",
                "source": "bitext",
                "split": "train",
                "conversation_id": f"bitext-{index}",
                "channel": "email",
                "locale": "en",
                "source_label": f"{row.category}/{row.intent}",
                "label_method": "category_mapping",
            }
        )
    return _base_frame(rows)


def _read_any(path: Path) -> pd.DataFrame:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return pd.read_csv(path)
    if suffix in {".jsonl", ".ndjson"}:
        records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]
        return pd.DataFrame(records)
    if suffix == ".json":
        return pd.DataFrame(json.loads(path.read_text(encoding="utf-8")))
    raise ValueError(f"Unsupported dataset format: {path.suffix}")


SYNTHETIC_LABEL_MAP = {
    "Оплата": "payment",
    "Подписка": "subscription",
    "Аккаунт": "account",
    "Приложение": "app",
    "Рекомендации": "recommendations",
    "Контент": "content",
    "Другое": "other",
}


def load_synthetic(path: Path) -> pd.DataFrame:
    """Load the team's synthetic seed cases (text/label required)."""
    frame = _read_any(path)
    _require_columns(frame, ("text", "label"), "Synthetic file")
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(frame.itertuples(index=False)):
        text = clean_text(row.text)
        label = SYNTHETIC_LABEL_MAP.get(str(row.label), str(row.label))
        if not is_usable(text) or label not in LABELS:
            continue
        rows.append(
            {
                "id": f"synthetic-{index}",
                "text": text,
                "label": label,
                "label_quality": "synthetic",
                "source": "synthetic",
                "split": "train",
                "conversation_id": f"synthetic-{index}",
                "channel": "app",
                "locale": "ru",
                "source_label": label,
                "label_method": "manual_synthetic",
            }
        )
    return _base_frame(rows)


def load_human(path: Path) -> pd.DataFrame:
    """Load human-verified cases with explicit splits."""
    frame = _read_any(path)
    _require_columns(frame, ("text", "label", "split"), "Human-verified file")
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(frame.itertuples(index=False)):
        text = clean_text(row.text)
        label = str(row.label)
        split = str(row.split)
        if not is_usable(text) or label not in LABELS or split not in {"train", "validation", "test"}:
            continue
        identifier = str(getattr(row, "id", f"human-{index}"))
        rows.append(
            {
                "id": identifier,
                "text": text,
                "label": label,
                "label_quality": "human_verified",
                "source": "human",
                "split": split,
                "conversation_id": str(getattr(row, "conversation_id", identifier)),
                "channel": str(getattr(row, "channel", "twitter")),
                "locale": str(getattr(row, "locale", "en")),
                "source_label": label,
                "label_method": "human",
            }
        )
    return _base_frame(rows)
