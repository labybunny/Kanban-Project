import os

import pytest

from app.ai_client import call_openrouter_chat


@pytest.mark.skipif(
    os.getenv("RUN_LIVE_AI_TEST") != "1",
    reason="Set RUN_LIVE_AI_TEST=1 to run live OpenRouter connectivity test",
)
def test_live_openrouter_connectivity_2_plus_2() -> None:
    if not os.getenv("OPENROUTER_API_KEY"):
        pytest.skip("OPENROUTER_API_KEY not configured for live connectivity test")

    output = call_openrouter_chat("What is 2+2? Reply with just the number.")

    assert "4" in output
