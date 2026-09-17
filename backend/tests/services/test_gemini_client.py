import httpx
import pytest
import respx

from backend.app.services.gemini_client import GeminiClient, GeminiClientError

BASE_URL = "https://generativelanguage.googleapis.com/v1beta"
API_KEY = "test-api-key"


@pytest.mark.asyncio
async def test_generate_embeddings_sends_text_and_returns_values() -> None:
    with respx.mock(base_url=BASE_URL, assert_all_mocked=True) as router:
        route = router.post("/models/text-embedding-004:embedContent").mock(
            return_value=httpx.Response(200, json={"embedding": {"values": [0.1, 0.2]}})
        )

        async with GeminiClient(api_key=API_KEY, base_url=BASE_URL) as client:
            result = await client.generate_embeddings("How does this card work?")

    assert result == [0.1, 0.2]
    assert route.called
    assert route.calls[0].request.url.params["key"] == API_KEY
    assert route.calls[0].request.content == (
        b'{"content":{"parts":[{"text":"How does this card work?"}]}}'
    )


@pytest.mark.asyncio
async def test_generate_response_sends_prompt_and_returns_text() -> None:
    with respx.mock(base_url=BASE_URL, assert_all_mocked=True) as router:
        route = router.post("/models/gemini-1.5-flash:generateContent").mock(
            return_value=httpx.Response(
                200,
                json={
                    "candidates": [
                        {"content": {"parts": [{"text": "Draw two cards."}]}}
                    ]
                },
            )
        )

        async with GeminiClient(api_key=API_KEY, base_url=BASE_URL) as client:
            result = await client.generate_response("Answer from the rules.")

    assert result == "Draw two cards."
    assert route.called
    assert route.calls[0].request.content == (
        b'{"contents":[{"parts":[{"text":"Answer from the rules."}]}]}'
    )


@pytest.mark.asyncio
async def test_api_errors_are_wrapped() -> None:
    with respx.mock(base_url=BASE_URL, assert_all_mocked=True) as router:
        router.post("/models/text-embedding-004:embedContent").mock(
            return_value=httpx.Response(401, json={"error": {"message": "Invalid key"}})
        )

        async with GeminiClient(api_key=API_KEY, base_url=BASE_URL) as client:
            with pytest.raises(GeminiClientError, match="request failed"):
                await client.generate_embeddings("text")


@pytest.mark.asyncio
async def test_timeouts_are_wrapped() -> None:
    with respx.mock(base_url=BASE_URL, assert_all_mocked=True) as router:
        router.post("/models/gemini-1.5-flash:generateContent").mock(
            side_effect=httpx.ReadTimeout("request timed out")
        )

        async with GeminiClient(api_key=API_KEY, base_url=BASE_URL) as client:
            with pytest.raises(GeminiClientError, match="request failed"):
                await client.generate_response("text")


@pytest.mark.asyncio
async def test_missing_api_key_is_rejected_before_request() -> None:
    with respx.mock(base_url=BASE_URL, assert_all_mocked=True) as router:
        async with GeminiClient(api_key="", base_url=BASE_URL) as client:
            with pytest.raises(GeminiClientError, match="not configured"):
                await client.generate_response("text")

    assert not router.calls
