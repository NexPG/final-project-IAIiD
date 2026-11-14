"""Shared dataset schema for the triage project."""

from __future__ import annotations

from typing import Final

LABELS: Final[tuple[str, ...]] = (
    "payment",
    "subscription",
    "account",
    "app",
    "recommendations",
    "content",
    "other",
)

LABEL_TO_QUEUE: Final[dict[str, str]] = {
    "payment": "billing",
    "subscription": "subscriptions",
    "account": "account_support",
    "app": "technical_support",
    "recommendations": "recommendations",
    "content": "content_support",
    "other": "general_support",
}

SPLITS: Final[tuple[str, ...]] = ("train", "validation", "test")
SOURCES: Final[tuple[str, ...]] = (
    "weak_twcs",
    "bitext",
    "synthetic",
    "human",
    "external_audio",
)
LABEL_QUALITIES: Final[tuple[str, ...]] = ("human_verified", "weak", "synthetic")
CHANNELS: Final[tuple[str, ...]] = ("twitter", "app", "web", "email", "chat")
LOCALES: Final[tuple[str, ...]] = ("en", "ru", "mixed")

REQUIRED_COLUMNS: Final[tuple[str, ...]] = (
    "id",
    "text",
    "label",
    "label_quality",
    "source",
    "split",
    "channel",
    "locale",
)


def queue_for(label: str) -> str:
    """Return the routing queue for a label."""
    try:
        return LABEL_TO_QUEUE[label]
    except KeyError as exc:
        raise ValueError(f"Unknown label: {label!r}") from exc
