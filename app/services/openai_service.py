"""
OpenAI service wrapper.

Design choice: every call is wrapped so failures are SPECIFIC.
No more "response generation failed" — you'll get the actual reason
(auth, rate limit, bad model name, network, etc).
"""
import logging
from openai import AsyncOpenAI, AuthenticationError, RateLimitError, APIConnectionError, APIStatusError

from app.core.config import settings

logger = logging.getLogger(__name__)

client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)


class OpenAIServiceError(Exception):
    """Raised with a clear, specific message — safe to show in API error responses."""
    pass


async def generate_response(system_prompt: str, user_message: str, history: list[dict] | None = None) -> str:
    """
    Calls OpenAI chat completion. Returns plain text.
    Raises OpenAIServiceError with a specific reason on failure.
    """
    messages = [{"role": "system", "content": system_prompt}]
    if history:
        messages.extend(history)
    messages.append({"role": "user", "content": user_message})

    try:
        response = await client.chat.completions.create(
            model=settings.OPENAI_CHAT_MODEL,
            messages=messages,
            temperature=0.7,
        )
    except AuthenticationError as e:
        logger.error(f"OpenAI auth failed: {e}")
        raise OpenAIServiceError(
            "OpenAI authentication failed. Check that OPENAI_API_KEY in .env is correct and active."
        ) from e
    except RateLimitError as e:
        logger.error(f"OpenAI rate limit: {e}")
        raise OpenAIServiceError(
            "OpenAI rate limit or quota exceeded. Check your usage/billing at platform.openai.com."
        ) from e
    except APIConnectionError as e:
        logger.error(f"OpenAI connection failed: {e}")
        raise OpenAIServiceError(
            "Could not reach OpenAI's API. Check your network/internet connection."
        ) from e
    except APIStatusError as e:
        logger.error(f"OpenAI API error {e.status_code}: {e.response}")
        raise OpenAIServiceError(
            f"OpenAI returned an error (status {e.status_code}). "
            f"This usually means a bad request — check the model name '{settings.OPENAI_CHAT_MODEL}' is valid."
        ) from e

    # Defensive check — if OpenAI ever returns an empty choices list
    if not response.choices:
        raise OpenAIServiceError("OpenAI returned no response choices. Try again.")

    content = response.choices[0].message.content
    if not content:
        raise OpenAIServiceError("OpenAI returned an empty message. Try again.")

    return content


async def generate_embedding(text: str) -> list[float]:
    """
    Generates a single embedding vector for the given text.
    Raises OpenAIServiceError with a specific reason on failure.
    """
    if not text or not text.strip():
        raise OpenAIServiceError("Cannot generate embedding for empty text.")

    try:
        response = await client.embeddings.create(
            model=settings.OPENAI_EMBEDDING_MODEL,
            input=text,
        )
    except AuthenticationError as e:
        raise OpenAIServiceError(
            "OpenAI authentication failed while generating embedding. Check OPENAI_API_KEY."
        ) from e
    except RateLimitError as e:
        raise OpenAIServiceError(
            "OpenAI rate limit or quota exceeded during embedding generation."
        ) from e
    except APIConnectionError as e:
        raise OpenAIServiceError(
            "Could not reach OpenAI's API for embedding generation. Check network."
        ) from e
    except APIStatusError as e:
        raise OpenAIServiceError(
            f"OpenAI embedding request failed (status {e.status_code}). "
            f"Check model name '{settings.OPENAI_EMBEDDING_MODEL}' is valid."
        ) from e

    if not response.data:
        raise OpenAIServiceError("OpenAI returned no embedding data.")

    return response.data[0].embedding
