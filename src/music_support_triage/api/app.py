"""FastAPI application for music-support triage."""

from __future__ import annotations

import os
import time
import uuid
from pathlib import Path
from typing import Annotated, Any, cast

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest
from starlette.exceptions import HTTPException as StarletteHTTPException

from music_support_triage.api.schemas import (
    BatchRequest,
    BatchResponse,
    ClassifyRequest,
    ClassifyResponse,
    FeedbackRequest,
    FeedbackResponse,
    HealthResponse,
    ModelInfoResponse,
    TopKItem,
)
from music_support_triage.core.config import load_yaml, resolve_path
from music_support_triage.services.classifier import ModelNotReadyError, TriageService

REQUEST_COUNT = Counter(
    "http_requests_total", "HTTP requests", ["method", "path", "status"]
)
REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds", "HTTP request latency", ["method", "path"]
)
CLASSIFY_LATENCY = Histogram(
    "model_inference_seconds", "Model inference latency", ["status"]
)
MODEL_READY = Gauge("model_loaded", "1 when the model artifact is loaded")

DEFAULT_CONFIG = Path("configs/service.yaml")


def get_service(request: Request) -> TriageService:
    """Resolve the triage service from application state."""
    return cast(TriageService, request.app.state.service)


def _service_config(config_path: Path | None = None) -> dict[str, Any]:
    path = config_path or Path(os.getenv("SERVICE_CONFIG", DEFAULT_CONFIG))
    if not path.is_absolute():
        path = Path.cwd() / path
    if not path.exists():
        return {}
    return load_yaml(path)


def create_app(
    model_path: Path | None = None,
    service: TriageService | None = None,
    config_path: Path | None = None,
) -> FastAPI:
    """Create an application with injectable service, used by tests too."""
    config = _service_config(config_path)
    resolved_model = model_path or resolve_path(os.getenv("MODEL_PATH", "artifacts/model.joblib"))
    assert resolved_model is not None
    threshold = float(config.get("threshold", 0.70))
    margin_threshold = float(config.get("margin_threshold", 0.10))

    app = FastAPI(
        title="Music Support Triage",
        version="0.1.0",
        description="Classify music-streaming support messages and route them to a queue.",
    )
    app.state.service = service or TriageService(
        resolved_model, threshold=threshold, margin_threshold=margin_threshold
    )
    app.state.feedback_ids = set()

    if service is None:
        app.state.service.load()
    MODEL_READY.set(1 if app.state.service.ready else 0)

    @app.middleware("http")
    async def observe(request: Request, call_next: Any) -> Response:
        started = time.perf_counter()
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id
        status = 500
        try:
            response = await call_next(request)
            status = response.status_code
            response.headers["X-Request-ID"] = request_id
            return response
        finally:
            path = request.url.path
            REQUEST_COUNT.labels(request.method, path, str(status)).inc()
            REQUEST_LATENCY.labels(request.method, path).observe(time.perf_counter() - started)

    def error_body(request: Request, code: str, message: str, **extra: Any) -> dict[str, Any]:
        return {
            "error": {
                "code": code,
                "message": message,
                "request_id": getattr(request.state, "request_id", None),
                **extra,
            }
        }

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content=error_body(
                request,
                "VALIDATION_ERROR",
                "Request validation failed",
                details=jsonable_encoder(exc.errors()),
            ),
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        code = {404: "NOT_FOUND", 503: "MODEL_UNAVAILABLE"}.get(
            exc.status_code, "HTTP_ERROR"
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=error_body(request, code, str(exc.detail)),
        )

    @app.get("/healthcheck", response_model=HealthResponse)
    def healthcheck(svc: Annotated[TriageService, Depends(get_service)]) -> Any:
        info = svc.model_info()
        if not svc.ready:
            return JSONResponse(
                status_code=503,
                content={"status": "not_ready", "reason": info.get("load_error")},
            )
        return {"status": "ok", "model_version": info["model_version"]}

    @app.get("/model-info", response_model=ModelInfoResponse)
    def model_info(svc: Annotated[TriageService, Depends(get_service)]) -> dict[str, Any]:
        return svc.model_info()

    def _classify(request_id: str, payload: ClassifyRequest, svc: TriageService) -> ClassifyResponse:
        try:
            result = svc.classify(
                payload.text,
                subject=payload.subject,
                channel=payload.channel,
                locale=payload.locale,
            )
        except ModelNotReadyError as exc:
            CLASSIFY_LATENCY.labels("error").observe(0)
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        CLASSIFY_LATENCY.labels("ok").observe(result["latency_ms"] / 1000.0)
        return ClassifyResponse(
            request_id=request_id,
            topic=result["topic"],
            queue=result["queue"],
            confidence=result["confidence"],
            margin=result["margin"],
            needs_human_review=result["needs_human_review"],
            top_k=[TopKItem(**item) for item in result["top_k"]],
            model_version=result["model_version"],
            latency_ms=result["latency_ms"],
        )

    @app.post("/v1/classify", response_model=ClassifyResponse)
    def classify(
        payload: ClassifyRequest, svc: Annotated[TriageService, Depends(get_service)]
    ) -> ClassifyResponse:
        return _classify(str(uuid.uuid4()), payload, svc)

    @app.post("/v1/classify/batch", response_model=BatchResponse)
    def classify_batch(
        payload: BatchRequest, svc: Annotated[TriageService, Depends(get_service)]
    ) -> BatchResponse:
        request_id = str(uuid.uuid4())
        items = [_classify(str(uuid.uuid4()), item, svc) for item in payload.items]
        return BatchResponse(request_id=request_id, items=items)

    @app.post("/v1/feedback", response_model=FeedbackResponse)
    def feedback(
        payload: FeedbackRequest, svc: Annotated[TriageService, Depends(get_service)]
    ) -> FeedbackResponse:
        if not svc.ready:
            raise HTTPException(status_code=503, detail="Model is not ready")
        if payload.request_id in app.state.feedback_ids:
            return FeedbackResponse(status="already_accepted", request_id=payload.request_id)
        app.state.feedback_ids.add(payload.request_id)
        return FeedbackResponse(status="accepted", request_id=payload.request_id)

    @app.get("/metrics")
    def metrics() -> Response:
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

    return app


app = create_app()
