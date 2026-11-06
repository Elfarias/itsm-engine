import io
import json
from urllib.error import HTTPError, URLError

import pytest

from app.triage import openrouter_client
from app.triage.openrouter_client import (
    OpenRouterConfigurationError,
    OpenRouterUnavailable,
    request_interpretation,
)


def _proposal_payload() -> dict[str, object]:
    return {
        "service_candidate": "Serviço de endpoint",
        "asset_candidate": None,
        "impact": "ALTO",
        "urgency": "ALTA",
        "symptoms": ["Falha de autenticação"],
        "impact_evidence": ["Afeta todos os usuários"],
        "urgency_evidence": ["Operação parada"],
        "missing_information": [],
        "uncertainties": [],
        "technical_summary": "Falha ampla de autenticação.",
    }


def _completion_response(content: str) -> bytes:
    return json.dumps(
        {"choices": [{"message": {"content": content}}]}
    ).encode("utf-8")


def test_client_sends_schema_constrained_description_only_request(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-secret")
    monkeypatch.setenv("OPENROUTER_MODEL", "provider/test-model")
    proposal = _proposal_payload()
    calls: list[tuple[object, int]] = []

    def fake_urlopen(request: object, timeout: int) -> io.BytesIO:
        calls.append((request, timeout))
        return io.BytesIO(_completion_response(json.dumps(proposal)))

    monkeypatch.setattr(openrouter_client, "urlopen", fake_urlopen)

    result = request_interpretation(
        "Falha no acesso ao serviço",
        "Extraia fatos estruturados da descrição.",
    )

    assert len(calls) == 1
    request, timeout = calls[0]
    assert request.full_url == openrouter_client.OPENROUTER_CHAT_COMPLETIONS_URL
    assert request.get_method() == "POST"
    assert request.get_header("Authorization") == "Bearer test-secret"
    assert timeout == 30

    body = json.loads(request.data)
    assert body["model"] == "provider/test-model"
    assert body["messages"] == [
        {
            "role": "system",
            "content": "Extraia fatos estruturados da descrição.",
        },
        {"role": "user", "content": "Falha no acesso ao serviço"},
    ]
    assert body["stream"] is False
    assert body["provider"] == {"require_parameters": True}
    response_format = body["response_format"]
    assert response_format["type"] == "json_schema"
    assert response_format["json_schema"]["strict"] is True
    provider_schema = response_format["json_schema"]["schema"]
    assert "$defs" not in provider_schema
    assert "ticket_id" not in provider_schema["properties"]
    assert "priority" not in provider_schema["properties"]
    assert "target_team" not in provider_schema["properties"]
    assert provider_schema["required"] == list(provider_schema["properties"])
    assert provider_schema["additionalProperties"] is False
    assert result.service_candidate == "Serviço de endpoint"
    assert result.impact.value == "ALTO"


def test_client_maps_missing_config_and_provider_failures_without_retry(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.setenv("OPENROUTER_MODEL", "provider/test-model")
    calls: list[object] = []

    def fake_urlopen(request: object, timeout: int) -> io.BytesIO:
        calls.append(request)
        return io.BytesIO(b"")

    monkeypatch.setattr(openrouter_client, "urlopen", fake_urlopen)
    with pytest.raises(OpenRouterConfigurationError):
        request_interpretation("description", "instructions")
    assert calls == []

    monkeypatch.setenv("OPENROUTER_API_KEY", "test-secret")
    monkeypatch.delenv("OPENROUTER_MODEL", raising=False)
    with pytest.raises(OpenRouterConfigurationError):
        request_interpretation("description", "instructions")
    assert calls == []

    monkeypatch.setenv("OPENROUTER_MODEL", "provider/test-model")
    failures: tuple[BaseException, ...] = (
        TimeoutError("timed out"),
        HTTPError(
            openrouter_client.OPENROUTER_CHAT_COMPLETIONS_URL,
            429,
            "rate limited",
            None,
            io.BytesIO(b"provider error"),
        ),
        URLError("unavailable"),
    )
    for failure in failures:
        calls.clear()

        def failing_urlopen(request: object, timeout: int) -> io.BytesIO:
            calls.append(request)
            raise failure

        monkeypatch.setattr(openrouter_client, "urlopen", failing_urlopen)
        with pytest.raises(OpenRouterUnavailable):
            request_interpretation("description", "instructions")
        assert len(calls) == 1


def test_client_rejects_malformed_provider_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-secret")
    monkeypatch.setenv("OPENROUTER_MODEL", "provider/test-model")
    monkeypatch.setattr(
        openrouter_client,
        "urlopen",
        lambda request, timeout: io.BytesIO(b'{"choices": []}'),
    )

    with pytest.raises(openrouter_client.OpenRouterInvalidResponse):
        request_interpretation("description", "instructions")
