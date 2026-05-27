"""
Prompt builder — assembles the system prompt with retrieved context.

Constructs the full prompt that instructs the LLM to answer ONLY
using the provided context, with source attribution.
"""

import logging

logger = logging.getLogger(__name__)

# ── System prompt template (with context) ──────────────────────────
SYSTEM_PROMPT_TEMPLATE = """You are a friendly and helpful AI assistant for WebBee Global, an ecommerce integration platform.

CRITICAL RULES:
1. First, analyze the user's input. If the user's message is NOT a greeting/casual greeting (like "hi", "hello", "hey", etc.) AND is NOT about WebBee Global or its services, products, integrations, or e-commerce operations related to WebBee, you MUST respond with EXACTLY:
   "I can't answer about that. Just ask me if you want to know anything about WebBee."
   Do NOT provide any other response, explanation, or help for unrelated queries (such as writing code, recipes, general knowledge, math, history, questions about unrelated companies/people/topics, etc., even if the context contains matching keywords).
2. For greetings (hi, hello, hey, etc.) or general conversational messages, respond warmly and naturally. Introduce yourself as the WebBee assistant and offer to help with questions about WebBee's products and services.
3. For questions about WebBee, answer ONLY using the provided context below. Do not use any outside knowledge about WebBee.
4. If the context does not contain enough information to answer a WebBee-specific question, say:
   "I'm sorry, I couldn't find information about that on the WebBee website. Please visit https://www.webbeeglobal.com/ or contact support."
5. Always cite your sources when answering from context. At the end of your answer, list the sources you used in the format:
   **Sources:**
   - [Page Title](URL)
6. Never make up facts, features, pricing, or policies about WebBee.
7. Be concise and helpful. Use bullet points and formatting where appropriate.
8. Respond in the same language as the user's question.

CONTEXT:
{context_blocks}
"""

# ── Conversational prompt (no context needed) ──────────────────────
CONVERSATIONAL_SYSTEM_PROMPT = """You are a friendly and helpful AI assistant for WebBee Global, an ecommerce integration platform.

WebBee Global helps businesses streamline multi-channel ecommerce operations with integrations for Amazon, Shopify, eBay, Walmart, TikTok Shop, NetSuite, and more. Key products include:
- Auto Multi-Channel Fulfillment (MCF) — automates order fulfillment via Amazon FBA across sales channels
- MapMyChannel — multi-channel marketplace integration
- Robust NetSuite Integrator — connects NetSuite ERP with ecommerce platforms

CRITICAL RULES:
1. First, analyze the user's input. If the user's message is NOT a greeting or casual greeting (like "hi", "hello", "how are you", "who are you", etc.) AND is NOT about WebBee Global or its services, products, integrations, or e-commerce operations, you MUST respond with EXACTLY:
   "I can't answer about that. Just ask me if you want to know anything about WebBee."
   Do NOT provide any other response, explanation, or help for unrelated queries (such as writing code, recipes, general knowledge, math, history, questions about unrelated companies/people/topics, jokes, etc.).
2. Respond warmly and naturally to greetings and casual conversation.
3. Introduce yourself as the WebBee Global assistant when appropriate.
4. Keep responses concise, friendly, and professional.
5. If someone asks a specific question about WebBee products, features, pricing, or policies, encourage them to ask so you can look it up in the knowledge base.
6. Respond in the same language as the user's question.
"""

NO_CONTEXT_RESPONSE = (
    "I'm sorry, I couldn't find specific information about that on the WebBee website. "
    "Could you rephrase your question? I can help with topics like WebBee's products, "
    "integrations, pricing, fulfillment services, and more. "
    "You can also visit https://www.webbeeglobal.com/ or contact their support team."
)


def build_context_block(chunk: dict) -> str:
    """Format a single chunk as a context block."""
    return (
        f"[Source: {chunk['page_title']} | {chunk['source_url']}]\n"
        f"{chunk['text']}\n"
        f"---"
    )


def build_prompt(chunks: list[dict], user_query: str) -> dict:
    """
    Build the full prompt for the LLM.
    
    Args:
        chunks: List of retrieved chunks with text and metadata
        user_query: The user's original question
        
    Returns:
        Dict with 'system_prompt' and 'user_message' keys,
        or None if no context is available.
    """
    if not chunks:
        logger.info("No context chunks provided — will return fallback response")
        return None

    # Build context blocks
    context_blocks = "\n\n".join(
        build_context_block(chunk) for chunk in chunks
    )

    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(context_blocks=context_blocks)

    logger.info(
        f"Built prompt with {len(chunks)} context blocks "
        f"({len(system_prompt)} chars system prompt)"
    )

    return {
        "system_prompt": system_prompt,
        "user_message": user_query,
    }


def get_no_context_response() -> str:
    """Return the standard no-context-found message."""
    return NO_CONTEXT_RESPONSE


def build_conversational_prompt(user_query: str) -> dict:
    """
    Build a prompt for generic/conversational messages (greetings, etc.)
    that don't need vector store context.
    
    Args:
        user_query: The user's message
        
    Returns:
        Dict with 'system_prompt' and 'user_message' keys
    """
    logger.info("Building conversational prompt (no context needed)")
    return {
        "system_prompt": CONVERSATIONAL_SYSTEM_PROMPT,
        "user_message": user_query,
    }
