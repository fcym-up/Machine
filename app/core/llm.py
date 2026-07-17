"""DeepSeek LLM client.

Uses centralized config via app.core.config.settings.
"""
from loguru import logger
from collections.abc import AsyncGenerator
from openai import AsyncOpenAI, OpenAI
from app.core.config import settings

LLM_API_KEY = settings.LLM_API_KEY
LLM_BASE_URL = settings.LLM_BASE_URL
LLM_MODEL = settings.LLM_MODEL


def get_llm_client() -> OpenAI | None:
    """Get LLM client instance. Returns None if API key not configured."""
    if not LLM_API_KEY:
        logger.warning("LLM_API_KEY not configured, Agent will fall back to rule engine")
        return None
    return OpenAI(api_key=LLM_API_KEY, base_url=LLM_BASE_URL)


def chat(
    messages: list[dict],
    model: str | None = None,
    temperature: float = 0.7,
) -> str | None:
    """Send chat request to LLM."""
    client = get_llm_client()
    if client is None:
        return None
    try:
        response = client.chat.completions.create(
            model=model or LLM_MODEL,
            messages=messages,
            temperature=temperature,
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"LLM call failed: {e}")
        return None


def chat_simple(prompt: str, system: str | None = None) -> str | None:
    """Simplified LLM call."""
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    return chat(messages)


async def chat_stream(prompt: str, system: str | None = None) -> AsyncGenerator[str]:
    """Streaming chat with sentence-level yield.

    Uses AsyncOpenAI for non-blocking token streaming.
    Yields complete sentences as they form.
    """
    if not LLM_API_KEY:
        logger.warning("LLM_API_KEY not configured, cannot stream")
        return

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    client = AsyncOpenAI(api_key=LLM_API_KEY, base_url=LLM_BASE_URL)

    try:
        stream = await client.chat.completions.create(
            model=LLM_MODEL,
            messages=messages,
            stream=True,
            temperature=0.7,
        )
        buffer = ""
        async for chunk in stream:
            delta = chunk.choices[0].delta.content if chunk.choices else None
            if delta:
                buffer += delta
                # Yield complete sentences
                while True:
                    boundary = None
                    for sep in ("。", "！", "？", "\n"):
                        idx = buffer.find(sep)
                        if idx != -1 and (boundary is None or idx < boundary[0]):
                            boundary = (idx, sep)
                    if boundary is None:
                        break
                    idx, sep = boundary
                    sentence = buffer[:idx + 1]
                    buffer = buffer[idx + 1:]
                    if sentence.strip():
                        yield sentence
                # Flush long segments without punctuation
                if len(buffer) >= 40:
                    yield buffer
                    buffer = ""
        # Yield remaining
        if buffer.strip():
            yield buffer
    except Exception as e:
        logger.error(f"LLM stream failed: {e}")
        return
