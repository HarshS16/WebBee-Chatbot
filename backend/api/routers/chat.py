"""
Chat router — handles the /api/chat endpoint.

Orchestrates the full RAG pipeline: retrieve → build prompt → generate.
Also handles generic conversational messages (greetings, thanks, etc.)
by routing them to the LLM with a conversational prompt.
"""

import logging
import re
import time
from fastapi import APIRouter, HTTPException

from api.models.schemas import ChatRequest, ChatResponse, SourceInfo
from api.services.retriever import retrieve
from api.services.prompt_builder import build_prompt, get_no_context_response, build_conversational_prompt
from api.services.groq_client import get_completion

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["chat"])

# ── Patterns for generic/conversational messages ───────────────────
GREETING_PATTERNS = [
    r"^(hi|hello|hey|hola|namaste|howdy|sup|yo|hii+|heyy+|helloo+)[\s!.,?]*$",
    r"^(good\s*(morning|afternoon|evening|night|day))[\s!.,?]*$",
    r"^(thanks|thank\s*you|thx|ty|thankyou)[\s!.,?]*$",
    r"^(bye|goodbye|see\s*you|take\s*care|cya)[\s!.,?]*$",
    r"^(how\s*are\s*you|how\s*do\s*you\s*do|what'?s\s*up|wassup|whats\s*up)[\s!?.,]*$",
    r"^(who\s*are\s*you|what\s*are\s*you|what\s*can\s*you\s*do|what\s*do\s*you\s*do)[\s!?.,]*$",
    r"^(help|help\s*me)[\s!?.,]*$",
    r"^(ok|okay|sure|great|cool|nice|awesome|got\s*it|understood|alright)[\s!.,?]*$",
]

COMPILED_GREETING_PATTERNS = [re.compile(p, re.IGNORECASE) for p in GREETING_PATTERNS]


def is_conversational_message(message: str) -> bool:
    """Check if a message is a generic greeting or conversational message."""
    cleaned = message.strip()
    for pattern in COMPILED_GREETING_PATTERNS:
        if pattern.match(cleaned):
            return True
    return False


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Process a user chat message through the RAG pipeline.
    
    1. Check if message is a generic greeting/conversational message
    2. Retrieve relevant chunks from ChromaDB
    3. Build context-grounded prompt (or conversational prompt)
    4. Generate response via Groq LLM
    5. Return answer with source citations
    """
    start_time = time.time()
    user_message = request.message.strip()

    logger.info(f"Chat request: '{user_message[:100]}' (session: {request.session_id})")

    # ── Step 1: Check for conversational messages ──────────────────
    if is_conversational_message(user_message):
        logger.info("Detected conversational message — routing to LLM directly")
        prompt_data = build_conversational_prompt(user_message)
        
        try:
            result = get_completion(
                system_prompt=prompt_data["system_prompt"],
                user_message=prompt_data["user_message"],
            )
        except Exception as e:
            logger.error(f"Groq error on conversational message: {e}")
            raise HTTPException(status_code=502, detail="Error generating response from AI")

        elapsed = round(time.time() - start_time, 2)
        logger.info(f"Response time: {elapsed}s (conversational)")

        if "error" in result:
            return ChatResponse(answer=result["error"], sources=[], found_context=False)

        return ChatResponse(
            answer=result["content"],
            sources=[],
            found_context=False,
        )

    # ── Step 2: Retrieve relevant chunks ───────────────────────────
    try:
        chunks = retrieve(user_message)
    except Exception as e:
        logger.error(f"Retrieval error: {e}")
        raise HTTPException(status_code=500, detail="Error searching the knowledge base")

    # ── Step 3: Handle no-context case ─────────────────────────────
    if not chunks:
        logger.info("No relevant context found — sending to LLM with conversational prompt")
        # Instead of a hardcoded fallback, let the LLM handle it conversationally
        prompt_data = build_conversational_prompt(user_message)

        try:
            result = get_completion(
                system_prompt=prompt_data["system_prompt"],
                user_message=prompt_data["user_message"],
            )
        except Exception as e:
            logger.error(f"Groq error on no-context fallback: {e}")
            # If LLM also fails, return the static fallback
            elapsed = round(time.time() - start_time, 2)
            logger.info(f"Response time: {elapsed}s (fallback)")
            return ChatResponse(
                answer=get_no_context_response(),
                sources=[],
                found_context=False,
            )

        elapsed = round(time.time() - start_time, 2)
        logger.info(f"Response time: {elapsed}s (no context, LLM response)")

        if "error" in result:
            return ChatResponse(answer=get_no_context_response(), sources=[], found_context=False)

        return ChatResponse(
            answer=result["content"],
            sources=[],
            found_context=False,
        )

    # ── Step 4: Build prompt ───────────────────────────────────────
    prompt_data = build_prompt(chunks, user_message)

    # ── Step 5: Generate response via Groq ─────────────────────────
    try:
        result = get_completion(
            system_prompt=prompt_data["system_prompt"],
            user_message=prompt_data["user_message"],
        )
    except Exception as e:
        logger.error(f"Groq error: {e}")
        raise HTTPException(status_code=502, detail="Error generating response from AI")

    # Handle Groq errors
    if "error" in result:
        logger.warning(f"Groq returned error: {result['error']}")
        return ChatResponse(
            answer=result["error"],
            sources=[],
            found_context=True,  # We found context but couldn't generate
        )

    # ── Step 6: Build source citations ─────────────────────────────
    # Deduplicate sources by URL
    seen_urls = set()
    sources = []
    
    for chunk in chunks:
        url = chunk["source_url"]
        if url not in seen_urls:
            seen_urls.add(url)
            sources.append(SourceInfo(
                title=chunk["page_title"],
                url=url,
                snippet=chunk["text"][:150] + "..." if len(chunk["text"]) > 150 else chunk["text"],
            ))

    elapsed = round(time.time() - start_time, 2)
    logger.info(f"Response time: {elapsed}s | Sources: {len(sources)}")

    return ChatResponse(
        answer=result["content"],
        sources=sources,
        found_context=True,
    )
