import json
import os
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from pydantic import ValidationError

from app.triage.interpretation_schemas import InterpretationProposal


OPENROUTER_CHAT_COMPLETIONS_URL = (
    "https://openrouter.ai/api/v1/chat/completions"
)
OPENROUTER_TIMEOUT_SECONDS = 30


class OpenRouterError(Exception):
    pass


class OpenRouterConfigurationError(OpenRouterError):
    pass


class OpenRouterUnavailable(OpenRouterError):
    pass


class OpenRouterInvalidResponse(OpenRouterError):
    pass


def request_interpretation(
    description: str,
    system_instructions: str,
) -> InterpretationProposal:
    api_key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    model = os.environ.get("OPENROUTER_MODEL", "").strip()
    if not api_key or not model:
        raise OpenRouterConfigurationError(
            "OpenRouter API key and model must be configured"
        )

    body = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_instructions},
            {"role": "user", "content": description},
        ],
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": "ticket_interpretation",
                "strict": True,
                "schema": _openrouter_schema(),
            },
        },
        "provider": {"require_parameters": True},
        "stream": False,
    }
    request = Request(
        OPENROUTER_CHAT_COMPLETIONS_URL,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=OPENROUTER_TIMEOUT_SECONDS) as response:
            provider_response = json.loads(response.read())
    except HTTPError as error:
        raise OpenRouterUnavailable("OpenRouter request failed") from error
    except (TimeoutError, URLError, OSError) as error:
        raise OpenRouterUnavailable("OpenRouter request failed") from error
    except (json.JSONDecodeError, UnicodeDecodeError, TypeError) as error:
        raise OpenRouterInvalidResponse(
            "OpenRouter returned an invalid response"
        ) from error

    try:
        content = provider_response["choices"][0]["message"]["content"]
        proposal_data = json.loads(content)
        return InterpretationProposal.model_validate(proposal_data)
    except (IndexError, KeyError, TypeError, json.JSONDecodeError, ValidationError) as error:
        raise OpenRouterInvalidResponse(
            "OpenRouter returned an invalid interpretation"
        ) from error


def _openrouter_schema() -> dict[str, Any]:
    schema = InterpretationProposal.model_json_schema()
    definitions = schema.pop("$defs", {})
    for property_schema in schema["properties"].values():
        for variant in property_schema.get("anyOf", []):
            reference = variant.pop("$ref", None)
            if reference is not None:
                definition_name = reference.rsplit("/", maxsplit=1)[-1]
                variant.update(definitions[definition_name])
    return schema
