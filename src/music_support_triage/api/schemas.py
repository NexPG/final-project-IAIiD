"""Pydantic request and response schemas for the public API."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

Channel = Literal["web", "email", "social", "app"]
Locale = Literal["en", "ru", "mixed"]


class ClassifyRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str = Field(min_length=1, max_length=5000)
    subject: str | None = Field(default=None, max_length=300)
    channel: Channel = "app"
    locale: Locale = "en"

    @field_validator("text")
    @classmethod
    def text_must_not_be_blank(cls, value: str) -> str:
        stripped = value.strip()
        if len(stripped) < 10:
            raise ValueError("text must contain at least 10 non-space characters")
        return stripped


class TopKItem(BaseModel):
    label: str
    confidence: float


class ClassifyResponse(BaseModel):
    request_id: str
    topic: str
    queue: str
    confidence: float
    margin: float
    needs_human_review: bool
    top_k: list[TopKItem]
    model_version: str
    latency_ms: float


class BatchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[ClassifyRequest] = Field(min_length=1, max_length=100)


class BatchResponse(BaseModel):
    request_id: str
    items: list[ClassifyResponse]


class FeedbackRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    request_id: str = Field(min_length=1, max_length=100)
    correct_topic: str | None = None
    comment: str | None = Field(default=None, max_length=1000)


class FeedbackResponse(BaseModel):
    status: str
    request_id: str


class HealthResponse(BaseModel):
    status: str
    model_version: str | None = None
    reason: str | None = None


class ModelInfoResponse(BaseModel):
    ready: bool
    model_version: str
    model_type: str
    trained_at: str | None
    n_train: int | None
    labels: list[str]
    threshold: float
    margin_threshold: float
    load_error: str | None
