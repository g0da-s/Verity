"""Retry utility for Groq API calls with backoff on rate limits."""

import asyncio
import groq
from langchain_core.messages import BaseMessage


class RateLimitExceeded(Exception):
    """Raised when all retries are exhausted due to rate limiting."""
    pass


async def invoke_with_retry(llm, messages: list[BaseMessage], max_retries: int = 3) -> BaseMessage:
    """Invoke an LLM with automatic retry on Groq 429 rate-limit errors.

    Reads the Retry-After header from the response to know how long to wait.
    Falls back to exponential backoff (2s, 4s, 8s) if the header is missing.

    Args:
        llm: A LangChain ChatGroq instance.
        messages: The messages to send.
        max_retries: Number of retry attempts before giving up.

    Returns:
        The LLM response message.

    Raises:
        RateLimitExceeded: If all retries are exhausted.
    """
    for attempt in range(max_retries + 1):
        try:
            return await llm.ainvoke(messages)
        except groq.RateLimitError as e:
            if attempt == max_retries:
                raise RateLimitExceeded(
                    "Groq API rate limit reached. Please try again in a minute."
                ) from e

            # Try to read Retry-After from the response headers
            wait = 2 ** (attempt + 1)  # fallback: 2s, 4s, 8s
            if hasattr(e, "response") and e.response is not None:
                retry_after = e.response.headers.get("retry-after")
                if retry_after:
                    try:
                        wait = int(retry_after)
                    except (ValueError, TypeError):
                        pass

            print(f"⏳ Rate limited (attempt {attempt + 1}/{max_retries}). Waiting {wait}s...")
            await asyncio.sleep(wait)
