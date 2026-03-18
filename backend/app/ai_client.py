from __future__ import annotations

import os
import json
from typing import Any

import httpx

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_MODEL = "arcee-ai/trinity-large-preview:free"


class OpenRouterConfigurationError(Exception):
    pass


class OpenRouterRequestError(Exception):
    pass


class OpenRouterStructuredOutputError(OpenRouterRequestError):
    pass


def _extract_content_text(content: Any) -> str:
    if isinstance(content, str):
        return content.strip()

    if isinstance(content, list):
        text_parts: list[str] = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                text = item.get("text")
                if isinstance(text, str):
                    text_parts.append(text)
        return "".join(text_parts).strip()

    return ""


def _post_openrouter(
    payload: dict[str, Any],
    *,
    api_key: str | None = None,
    timeout_seconds: float = 20.0,
    transport: httpx.BaseTransport | None = None,
) -> dict[str, Any]:
    resolved_api_key = api_key or os.getenv("OPENROUTER_API_KEY")
    if not resolved_api_key:
        raise OpenRouterConfigurationError("OPENROUTER_API_KEY is not configured")

    headers = {
        "Authorization": f"Bearer {resolved_api_key}",
        "Content-Type": "application/json",
    }

    try:
        with httpx.Client(timeout=timeout_seconds, transport=transport) as client:
            response = client.post(OPENROUTER_URL, headers=headers, json=payload)
    except httpx.RequestError as error:
        raise OpenRouterRequestError("Could not reach OpenRouter") from error

    if response.status_code >= 400:
        response_excerpt = response.text[:200]
        raise OpenRouterRequestError(
            f"OpenRouter error ({response.status_code}): {response_excerpt}"
        )

    try:
        return response.json()
    except ValueError as error:
        raise OpenRouterRequestError("OpenRouter response was not valid JSON") from error


def call_openrouter_chat(
    prompt: str,
    *,
    api_key: str | None = None,
    timeout_seconds: float = 20.0,
    transport: httpx.BaseTransport | None = None,
) -> str:
    payload = {
        "model": OPENROUTER_MODEL,
        "messages": [{"role": "user", "content": prompt}],
    }

    body = _post_openrouter(
        payload,
        api_key=api_key,
        timeout_seconds=timeout_seconds,
        transport=transport,
    )
    try:
        content = body["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError, ValueError) as error:
        raise OpenRouterRequestError("OpenRouter response format was invalid") from error

    text = _extract_content_text(content)
    if not text:
        raise OpenRouterRequestError("OpenRouter returned an empty response")

    return text


def call_openrouter_structured_json(
    *,
    messages: list[dict[str, str]],
    schema_name: str,
    schema: dict[str, Any],
    api_key: str | None = None,
    timeout_seconds: float = 20.0,
    transport: httpx.BaseTransport | None = None,
) -> dict[str, Any]:
    payload = {
        "model": OPENROUTER_MODEL,
        "messages": messages,
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": schema_name,
                "strict": True,
                "schema": schema,
            },
        },
    }
    body = _post_openrouter(
        payload,
        api_key=api_key,
        timeout_seconds=timeout_seconds,
        transport=transport,
    )
    try:
        content = body["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError, ValueError) as error:
        raise OpenRouterStructuredOutputError("Structured response format was invalid") from error

    text = _extract_content_text(content)
    if not text:
        raise OpenRouterStructuredOutputError("Structured response content was empty")

    try:
        parsed = json.loads(text)
    except ValueError as error:
        raise OpenRouterStructuredOutputError("Structured response was not valid JSON") from error

    if not isinstance(parsed, dict):
        raise OpenRouterStructuredOutputError("Structured response root must be an object")
    return parsed
