"""
Groq API client wrapper.

Handles communication with the Groq inference API, including
error handling for rate limits and connection issues.
"""

import logging
import os

from dotenv import load_dotenv
from groq import Groq, RateLimitError, APIError, APIConnectionError

load_dotenv()

logger = logging.getLogger(__name__)

# ── Configuration ──────────────────────────────────────────────────
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
MAX_TOKENS = int(os.getenv("MAX_TOKENS", 800))
TEMPERATURE = float(os.getenv("TEMPERATURE", 0.1))


def _get_client() -> Groq:
    """Get a Groq client instance."""
    if not GROQ_API_KEY or GROQ_API_KEY == "your_groq_api_key_here":
        raise ValueError(
            "GROQ_API_KEY is not configured. "
            "Please set it in the .env file. "
            "Get a key at https://console.groq.com/"
        )
    return Groq(api_key=GROQ_API_KEY)


def get_completion(system_prompt: str, user_message: str) -> dict:
    """
    Get a chat completion from Groq.
    
    Args:
        system_prompt: System prompt with context
        user_message: User's question
        
    Returns:
        Dict with 'content' (str) and 'usage' (dict) keys.
        On error, returns dict with 'error' (str) key.
    """
    try:
        client = _get_client()

        logger.info(f"Calling Groq ({GROQ_MODEL}) — temp={TEMPERATURE}, max_tokens={MAX_TOKENS}")

        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            max_tokens=MAX_TOKENS,
            temperature=TEMPERATURE,
        )

        content = response.choices[0].message.content
        usage = {
            "prompt_tokens": response.usage.prompt_tokens,
            "completion_tokens": response.usage.completion_tokens,
            "total_tokens": response.usage.total_tokens,
        }

        logger.info(f"Groq response: {len(content)} chars, {usage['total_tokens']} tokens")

        return {
            "content": content,
            "usage": usage,
        }

    except RateLimitError as e:
        logger.warning(f"Groq rate limit hit: {e}")
        return {
            "error": (
                "I'm currently experiencing high demand. "
                "Please wait a moment and try again. "
                "(Rate limit reached)"
            )
        }

    except APIConnectionError as e:
        logger.error(f"Groq connection error: {e}")
        return {
            "error": (
                "I'm having trouble connecting to the AI service. "
                "Please try again in a few moments."
            )
        }

    except APIError as e:
        logger.error(f"Groq API error: {e}")
        return {
            "error": f"An error occurred with the AI service: {str(e)}"
        }

    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        return {
            "error": str(e)
        }

    except Exception as e:
        logger.error(f"Unexpected error calling Groq: {e}")
        return {
            "error": "An unexpected error occurred. Please try again."
        }
