import httpx
import pytest

from app.ai_client import (
    OpenRouterConfigurationError,
    OpenRouterRequestError,
    OpenRouterStructuredOutputError,
    call_openrouter_chat,
    call_openrouter_structured_json,
)


def test_call_openrouter_chat_success() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith("/chat/completions")
        return httpx.Response(
            status_code=200,
            json={"choices": [{"message": {"content": "4"}}]},
        )

    transport = httpx.MockTransport(handler)
    output = call_openrouter_chat(
        "What is 2+2?",
        api_key="test-key",
        transport=transport,
    )

    assert output == "4"


def test_call_openrouter_chat_missing_api_key() -> None:
    with pytest.raises(OpenRouterConfigurationError, match="OPENROUTER_API_KEY"):
        call_openrouter_chat("What is 2+2?", api_key="")


def test_call_openrouter_chat_provider_error() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(
            status_code=401,
            text='{"error":"invalid key"}',
        )

    transport = httpx.MockTransport(handler)

    with pytest.raises(OpenRouterRequestError, match="OpenRouter error"):
        call_openrouter_chat("What is 2+2?", api_key="test-key", transport=transport)


def test_call_openrouter_structured_json_success() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(
            status_code=200,
            json={
                "choices": [
                    {
                        "message": {
                            "content": '{"assistantResponse":"Done","operations":[]}'
                        }
                    }
                ]
            },
        )

    payload = call_openrouter_structured_json(
        messages=[{"role": "user", "content": "Test"}],
        schema_name="test_schema",
        schema={"type": "object"},
        api_key="test-key",
        transport=httpx.MockTransport(handler),
    )

    assert payload["assistantResponse"] == "Done"
    assert payload["operations"] == []


def test_call_openrouter_structured_json_invalid_json() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(
            status_code=200,
            json={
                "choices": [
                    {
                        "message": {
                            "content": "not-json"
                        }
                    }
                ]
            },
        )

    with pytest.raises(OpenRouterStructuredOutputError, match="valid JSON"):
        call_openrouter_structured_json(
            messages=[{"role": "user", "content": "Test"}],
            schema_name="test_schema",
            schema={"type": "object"},
            api_key="test-key",
            transport=httpx.MockTransport(handler),
        )
