from typing import Any

from fastapi.testclient import TestClient

from music_support_triage.api.app import create_app


class FakeService:
    ready = True

    def model_info(self) -> dict[str, Any]:
        return {
            "ready": True,
            "model_version": "fake-1",
            "model_type": "fake",
            "trained_at": "2026-11-14T00:00:00+00:00",
            "n_train": 10,
            "labels": [
                "payment",
                "subscription",
                "account",
                "app",
                "recommendations",
                "content",
                "other",
            ],
            "threshold": 0.7,
            "margin_threshold": 0.1,
            "load_error": None,
        }

    def classify(
        self,
        text: str,
        subject: str | None = None,
        channel: str | None = None,
        locale: str | None = None,
    ) -> dict[str, Any]:
        return {
            "topic": "payment",
            "queue": "billing",
            "confidence": 0.91,
            "margin": 0.8,
            "needs_human_review": False,
            "top_k": [
                {"label": "payment", "confidence": 0.91},
                {"label": "subscription", "confidence": 0.05},
                {"label": "account", "confidence": 0.02},
            ],
            "model_version": "fake-1",
            "latency_ms": 1.2,
        }


def client() -> TestClient:
    return TestClient(create_app(service=FakeService()))


def test_healthcheck_and_model_info() -> None:
    api = client()
    health = api.get("/healthcheck")
    assert health.status_code == 200
    assert health.json()["status"] == "ok"
    info = api.get("/model-info")
    assert info.status_code == 200
    assert info.json()["model_version"] == "fake-1"


def test_classify_contract() -> None:
    api = client()
    response = api.post(
        "/v1/classify",
        json={"text": "I was charged twice for my subscription", "channel": "app"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["topic"] == "payment"
    assert body["queue"] == "billing"
    assert body["request_id"]
    assert len(body["top_k"]) == 3


def test_classify_rejects_short_text() -> None:
    api = client()
    response = api.post("/v1/classify", json={"text": "short"})
    assert response.status_code == 422


def test_batch_preserves_order_and_feedback_is_idempotent() -> None:
    api = client()
    response = api.post(
        "/v1/classify/batch",
        json={"items": [{"text": "first message about payment"}, {"text": "second message about account"}]},
    )
    assert response.status_code == 200
    assert len(response.json()["items"]) == 2

    first = api.post("/v1/feedback", json={"request_id": "req-1"})
    second = api.post("/v1/feedback", json={"request_id": "req-1"})
    assert first.json()["status"] == "accepted"
    assert second.json()["status"] == "already_accepted"


def test_metrics_endpoint() -> None:
    api = client()
    api.get("/healthcheck")
    response = api.get("/metrics")
    assert response.status_code == 200
    assert "http_requests_total" in response.text


def test_validation_error_envelope_and_request_id() -> None:
    api = client()
    response = api.post("/v1/classify", json={"text": "short"})
    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "VALIDATION_ERROR"
    assert body["error"]["request_id"]
    assert response.headers["X-Request-ID"]


def test_not_found_envelope() -> None:
    api = client()
    response = api.get("/does-not-exist")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"


def test_openapi_contains_contract_paths() -> None:
    api = client()
    schema = api.get("/openapi.json").json()
    for path in (
        "/v1/classify",
        "/v1/classify/batch",
        "/v1/feedback",
        "/healthcheck",
        "/model-info",
        "/metrics",
    ):
        assert path in schema["paths"]
