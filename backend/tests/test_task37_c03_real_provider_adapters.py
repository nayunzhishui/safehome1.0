import importlib
import json
import socket
import sys
import threading
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = PROJECT_ROOT / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))


class RecordingTransport:
    def __init__(self):
        self.calls = []

    def post_json(
        self,
        url,
        *,
        headers,
        payload,
        connect_timeout_seconds,
        read_timeout_seconds,
        total_timeout_seconds,
        cancellation_token=None,
    ):
        self.calls.append(
            {
                "url": url,
                "headers": dict(headers),
                "payload": payload,
                "connect_timeout_seconds": connect_timeout_seconds,
                "read_timeout_seconds": read_timeout_seconds,
                "total_timeout_seconds": total_timeout_seconds,
                "cancellation_token": cancellation_token,
            }
        )
        return {
            "status_code": 200,
            "headers": {"x-request-id": "header-request-id"},
            "json": {
                "id": "provider-request-id",
                "model": "test-model-2026-07",
                "choices": [
                    {
                        "message": {
                            "content": "[S1] 已批准材料：先暂停并核对当下感受。"
                        }
                    }
                ],
                "usage": {
                    "prompt_tokens": 120,
                    "completion_tokens": 30,
                    "total_tokens": 150,
                },
            },
        }


def test_real_provider_without_server_secret_fails_closed(monkeypatch):
    module = importlib.import_module("services.ai_qa_provider")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("OPENAI_MODEL", "test-model")
    provider = module.get_provider(
        "openai",
        allow_real=True,
        transport=RecordingTransport(),
    )

    with pytest.raises(module.ProviderError) as exc_info:
        provider.generate(
            "如何暂停？",
            [{"title": "已批准材料", "excerpt": "先暂停。"}],
            timeout_seconds=2,
        )

    assert exc_info.value.code == "provider_secret_missing"
    assert "OPENAI_API_KEY" not in str(exc_info.value)


def test_openai_compatible_adapter_uses_server_secret_and_records_metadata(
    monkeypatch,
):
    module = importlib.import_module("services.ai_qa_provider")
    monkeypatch.setenv("OPENAI_API_KEY", "server-only-test-secret")
    monkeypatch.setenv("OPENAI_MODEL", "test-model")
    monkeypatch.setenv(
        "OPENAI_INPUT_COST_MICROS_PER_MILLION_TOKENS",
        "1000000",
    )
    monkeypatch.setenv(
        "OPENAI_OUTPUT_COST_MICROS_PER_MILLION_TOKENS",
        "2000000",
    )
    monkeypatch.setenv("OPENAI_COST_CURRENCY", "USD")
    transport = RecordingTransport()
    provider = module.get_provider(
        "openai",
        allow_real=True,
        transport=transport,
    )

    result = provider.generate(
        "如何暂停？",
        [{"title": "已批准材料", "excerpt": "先暂停。"}],
        timeout_seconds=3,
        connect_timeout_seconds=1,
        read_timeout_seconds=2,
    )

    assert result.provider == "openai"
    assert result.provider_request_id == "provider-request-id"
    assert result.model_version == "test-model-2026-07"
    assert result.input_tokens == 120
    assert result.output_tokens == 30
    assert result.token_estimate == 150
    assert result.cost_micros == 180
    assert result.cost_currency == "USD"
    assert transport.calls[0]["headers"]["Authorization"] == (
        "Bearer server-only-test-secret"
    )
    assert transport.calls[0]["payload"]["store"] is False
    serialized = json.dumps(result.__dict__, ensure_ascii=False)
    assert "server-only-test-secret" not in serialized


def test_stdlib_transport_timeout_closes_connection_without_background_call(
    monkeypatch,
):
    module = importlib.import_module("services.ai_qa_provider")
    connections = []

    class FakeResponse:
        status = 200

        def getheaders(self):
            return []

        def read(self, _size):
            raise socket.timeout("read timed out")

    class FakeConnection:
        def __init__(self, *_args, **_kwargs):
            self.closed = False
            self.sock = self
            connections.append(self)

        def settimeout(self, _value):
            return None

        def request(self, *_args, **_kwargs):
            return None

        def getresponse(self):
            return FakeResponse()

        def close(self):
            self.closed = True

    monkeypatch.setattr(module.http.client, "HTTPSConnection", FakeConnection)
    before_threads = {item.ident for item in threading.enumerate()}
    transport = module.StdlibJsonTransport(
        allowed_hosts={"api.openai.com"}
    )

    with pytest.raises(module.ProviderError) as exc_info:
        transport.post_json(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": "Bearer server-only"},
            payload={"model": "test"},
            connect_timeout_seconds=0.1,
            read_timeout_seconds=0.1,
            total_timeout_seconds=0.2,
        )

    after_threads = {item.ident for item in threading.enumerate()}
    assert exc_info.value.code == "provider_timeout"
    assert connections and connections[0].closed is True
    assert after_threads == before_threads


def _fresh_app(tmp_path, monkeypatch):
    for name in list(sys.modules):
        if name in {"app", "config", "database", "models"} or name.startswith(
            ("routes.", "services.")
        ):
            sys.modules.pop(name, None)
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "safehome-test.sqlite3"))
    monkeypatch.setenv("CONTENT_DIR", str(PROJECT_ROOT / "content"))
    monkeypatch.setenv("AI_QA_ENABLED", "0")
    monkeypatch.setenv("AI_QA_SANDBOX_ENABLED", "1")
    monkeypatch.setenv("AI_QA_PROVIDER", "fake")
    return importlib.import_module("app").app


def _researcher_headers(app):
    with app.app_context():
        database = importlib.import_module("database")
        auth_utils = importlib.import_module("routes.auth_utils")
        with database.get_connection() as conn:
            now = database.now_iso()
            conn.execute(
                """
                INSERT INTO users
                (id, nickname, role, source, status, created_at, updated_at)
                VALUES ('researcher-c03', 'researcher-c03', 'researcher',
                        'test', 'active', ?, ?)
                """,
                (now, now),
            )
            conn.commit()
        token = auth_utils.generate_auth_token(
            {"id": "researcher-c03", "role": "researcher"}
        )
    return {"Authorization": f"Bearer {token}"}


def test_client_cannot_select_real_provider(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    headers = _researcher_headers(app)
    session_response = client.post(
        "/api/ai-qa/sessions",
        json={
            "synthetic_data": True,
            "research_use_allowed": False,
            "use_case_id": "evidence_gap_check",
        },
        headers=headers,
    )
    session_id = session_response.get_json()["data"]["id"]

    response = client.post(
        f"/api/ai-qa/sessions/{session_id}/messages",
        json={
            "text": "如何暂停？",
            "synthetic_data": True,
            "provider": "openai",
        },
        headers=headers,
    )

    assert response.status_code == 409
    assert response.get_json()["error"]["code"] == (
        "ai_qa_provider_override_forbidden"
    )


def test_schema_052_records_provider_request_usage_without_raw_text(
    tmp_path, monkeypatch
):
    app = _fresh_app(tmp_path, monkeypatch)
    with app.app_context():
        database = importlib.import_module("database")
        with database.get_connection() as conn:
            columns = {
                row["name"]
                for row in conn.execute(
                    "PRAGMA table_info(ai_qa_provider_events)"
                ).fetchall()
            }

    assert database.CURRENT_SCHEMA_VERSION == "2026_07_28_052"
    assert database.CURRENT_SCHEMA_NAME == "ai_provider_runtime_metadata"
    assert {
        "provider_request_id",
        "input_tokens",
        "output_tokens",
        "cost_currency",
    }.issubset(columns)
    assert "request_text" not in columns
    assert "response_text" not in columns
