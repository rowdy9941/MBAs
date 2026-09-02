import json
import logging
import sys

from fastapi.testclient import TestClient

from app.config import Settings
from app.main import JsonFormatter, app


def client_without_lifespan() -> TestClient:
    return TestClient(app)


def test_cors_origins_are_trimmed_and_empty_values_removed():
    config = Settings(mbas_cors_origins="http://localhost:3000, https://app.example.com, ")
    assert config.cors_origins == ["http://localhost:3000", "https://app.example.com"]


def test_liveness_does_not_require_database():
    client = client_without_lifespan()
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_provider_health_does_not_expose_secrets():
    payload = client_without_lifespan().get("/v1/provider-health").json()
    assert payload["status"] == "ok"
    assert set(payload["providers"]) == {"sarvam", "whatsapp", "livekit"}


def test_correlation_id_is_preserved():
    response = client_without_lifespan().get("/healthz", headers={"X-Correlation-ID": "test-request-123"})
    assert response.headers["X-Correlation-ID"] == "test-request-123"


def test_correlation_id_is_generated_when_missing():
    response = client_without_lifespan().get("/healthz")
    assert response.headers["X-Correlation-ID"]


def test_json_formatter_includes_request_context():
    record = logging.LogRecord("mbas.api", logging.INFO, __file__, 1, "done", (), None)
    record.correlation_id = "abc"
    record.status_code = 200
    payload = json.loads(JsonFormatter().format(record))
    assert payload["message"] == "done"
    assert payload["timestamp"].endswith("Z")
    assert payload["correlation_id"] == "abc"
    assert payload["status_code"] == 200


def test_json_formatter_preserves_exception_details():
    try:
        raise RuntimeError("diagnostic failure")
    except RuntimeError:
        record = logging.LogRecord(
            "mbas.api", logging.ERROR, __file__, 1, "request.failed", (), sys.exc_info(),
        )

    payload = json.loads(JsonFormatter().format(record))
    assert "RuntimeError: diagnostic failure" in payload["exception"]


def test_failed_response_includes_correlation_id():
    path = "/_test/unhandled-error"

    async def fail():
        raise RuntimeError("must not leak")

    app.add_api_route(path, fail, methods=["GET"])
    response = client_without_lifespan().get(path, headers={"X-Correlation-ID": "failed-request-123"})

    assert response.status_code == 500
    assert response.headers["X-Correlation-ID"] == "failed-request-123"
    assert response.json() == {"detail": "Internal server error"}
