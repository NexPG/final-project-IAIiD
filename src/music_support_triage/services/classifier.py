"""In-process classification service used by the API and CLI."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from music_support_triage.data.schema import LABELS, queue_for
from music_support_triage.data.text import clean_text
from music_support_triage.models.baseline import load_model, predict_proba
from music_support_triage.services.routing import route, top_k


class ModelNotReadyError(RuntimeError):
    """Raised when the model artifact is missing or failed to load."""


class TriageService:
    """Load a model once and classify support messages."""

    def __init__(
        self,
        model_path: Path,
        threshold: float = 0.70,
        margin_threshold: float = 0.10,
    ) -> None:
        self.model_path = model_path
        self.threshold = threshold
        self.margin_threshold = margin_threshold
        self._pipeline: Any = None
        self._metadata: dict[str, Any] = {}
        self._load_error: str | None = None

    def load(self) -> None:
        """Load the model artifact; keep the error for readiness reporting."""
        try:
            self._pipeline, self._metadata = load_model(self.model_path)
            self._load_error = None
        except Exception as exc:  # noqa: BLE001 - readiness must expose the reason
            self._pipeline = None
            self._load_error = str(exc)

    @property
    def ready(self) -> bool:
        return self._pipeline is not None

    def model_info(self) -> dict[str, Any]:
        """Return model metadata for `/model-info`."""
        return {
            "ready": self.ready,
            "model_version": self._metadata.get("model_version", "unknown"),
            "model_type": self._metadata.get("model_type", "unknown"),
            "trained_at": self._metadata.get("trained_at"),
            "n_train": self._metadata.get("n_train"),
            "labels": list(LABELS),
            "threshold": self.threshold,
            "margin_threshold": self.margin_threshold,
            "load_error": self._load_error,
        }

    def classify(
        self,
        text: str,
        subject: str | None = None,
        channel: str | None = None,
        locale: str | None = None,
    ) -> dict[str, Any]:
        """Classify one message and return label, probabilities and routing."""
        if not self.ready:
            raise ModelNotReadyError(self._load_error or "Model is not loaded")

        cleaned = clean_text(text)
        started = time.perf_counter()
        probabilities = predict_proba(self._pipeline, [cleaned])[0]
        latency_ms = (time.perf_counter() - started) * 1000.0

        decision = route(
            probabilities,
            labels=LABELS,
            threshold=self.threshold,
            margin_threshold=self.margin_threshold,
        )
        return {
            "topic": decision.label,
            "queue": decision.queue,
            "confidence": round(decision.confidence, 6),
            "margin": round(decision.margin, 6),
            "needs_human_review": decision.needs_human_review,
            "top_k": top_k(probabilities, LABELS, k=3),
            "model_version": str(self._metadata.get("model_version", "unknown")),
            "latency_ms": round(latency_ms, 3),
            "input": {
                "subject": subject,
                "channel": channel,
                "locale": locale,
                "cleaned_length": len(cleaned),
            },
            "queue_for_label": queue_for(decision.label),
        }
