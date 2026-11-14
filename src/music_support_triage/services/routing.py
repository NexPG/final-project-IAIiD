"""Confidence-based routing with a safe manual-review fallback."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from music_support_triage.data.schema import LABELS, queue_for

MANUAL_QUEUE = "manual_review"


@dataclass(frozen=True)
class RoutingDecision:
    """Result of applying confidence thresholds to model probabilities."""

    label: str
    confidence: float
    margin: float
    queue: str
    needs_human_review: bool

    def as_dict(self) -> dict[str, object]:
        return {
            "label": self.label,
            "confidence": round(self.confidence, 6),
            "margin": round(self.margin, 6),
            "queue": self.queue,
            "needs_human_review": self.needs_human_review,
        }


def top_k(probabilities: Sequence[float], labels: Sequence[str] = LABELS, k: int = 3) -> list[dict[str, object]]:
    """Return the top-k classes sorted by probability."""
    pairs = sorted(zip(labels, probabilities, strict=True), key=lambda item: item[1], reverse=True)
    return [{"label": label, "confidence": round(float(score), 6)} for label, score in pairs[:k]]


def route(
    probabilities: Sequence[float],
    labels: Sequence[str] = LABELS,
    threshold: float = 0.70,
    margin_threshold: float = 0.10,
) -> RoutingDecision:
    """Route a prediction to a queue or to manual review."""
    if len(probabilities) != len(labels):
        raise ValueError("probabilities and labels must have the same length")
    pairs = sorted(zip(labels, probabilities, strict=True), key=lambda item: item[1], reverse=True)
    label, confidence = pairs[0]
    second = pairs[1][1] if len(pairs) > 1 else 0.0
    margin = float(confidence - second)

    if confidence < threshold or margin < margin_threshold:
        return RoutingDecision(
            label=label,
            confidence=float(confidence),
            margin=margin,
            queue=MANUAL_QUEUE,
            needs_human_review=True,
        )

    if label == "other":
        return RoutingDecision(
            label=label,
            confidence=float(confidence),
            margin=margin,
            queue=queue_for(label),
            needs_human_review=False,
        )

    return RoutingDecision(
        label=label,
        confidence=float(confidence),
        margin=margin,
        queue=queue_for(label),
        needs_human_review=False,
    )
