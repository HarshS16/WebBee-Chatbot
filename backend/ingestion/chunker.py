"""
Token-aware text chunker with overlapping windows.

Splits text into chunks of approximately 400-600 tokens with
50-token overlap to ensure facts spanning chunk boundaries
are captured in at least one chunk.
"""

import os
import re
from dotenv import load_dotenv

load_dotenv()

# ── Configuration ──────────────────────────────────────────────────
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", 500))        # target tokens per chunk
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", 50))    # overlap tokens
SEPARATORS = ["\n\n", "\n", ". ", ", ", " "]           # split preference order


def _estimate_tokens(text: str) -> int:
    """
    Rough token estimation. ~1 token per 4 characters for English.
    More accurate than word count for transformer models.
    """
    return max(1, len(text) // 4)


def _split_by_separator(text: str, separator: str) -> list[str]:
    """Split text by separator, keeping the separator at the end of each chunk."""
    if separator == " ":
        return text.split(" ")
    
    parts = text.split(separator)
    # Re-attach separator to each part (except the last)
    result = []
    for i, part in enumerate(parts):
        if i < len(parts) - 1:
            result.append(part + separator)
        else:
            result.append(part)
    return [p for p in result if p.strip()]


def _recursive_split(text: str, separators: list[str], chunk_size: int) -> list[str]:
    """
    Recursively split text using a hierarchy of separators.
    
    Tries the first separator; if resulting chunks are still too large,
    recursively applies the next separator.
    """
    if _estimate_tokens(text) <= chunk_size:
        return [text]

    if not separators:
        # Last resort: hard split by character count
        char_limit = chunk_size * 4  # ~4 chars per token
        chunks = []
        while text:
            chunks.append(text[:char_limit])
            text = text[char_limit:]
        return chunks

    current_sep = separators[0]
    remaining_seps = separators[1:]

    parts = _split_by_separator(text, current_sep)

    chunks = []
    current_chunk = ""

    for part in parts:
        test_chunk = current_chunk + part if current_chunk else part
        
        if _estimate_tokens(test_chunk) <= chunk_size:
            current_chunk = test_chunk
        else:
            if current_chunk:
                chunks.append(current_chunk)
            
            # If the part itself is too large, split it further
            if _estimate_tokens(part) > chunk_size:
                sub_chunks = _recursive_split(part, remaining_seps, chunk_size)
                chunks.extend(sub_chunks[:-1])
                current_chunk = sub_chunks[-1] if sub_chunks else ""
            else:
                current_chunk = part

    if current_chunk:
        chunks.append(current_chunk)

    return chunks


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, chunk_overlap: int = CHUNK_OVERLAP) -> list[str]:
    """
    Split text into overlapping chunks.
    
    Args:
        text: Input text to chunk
        chunk_size: Target tokens per chunk (default 500)
        chunk_overlap: Overlap tokens between consecutive chunks (default 50)
        
    Returns:
        List of text chunk strings
    """
    if not text or not text.strip():
        return []

    # First, split into non-overlapping chunks
    raw_chunks = _recursive_split(text.strip(), SEPARATORS, chunk_size)

    if len(raw_chunks) <= 1:
        return raw_chunks

    # Apply overlap: prepend the tail of the previous chunk
    overlap_chars = chunk_overlap * 4  # ~4 chars per token
    overlapped_chunks = [raw_chunks[0]]

    for i in range(1, len(raw_chunks)):
        prev_chunk = raw_chunks[i - 1]
        current_chunk = raw_chunks[i]

        # Get the last N characters of the previous chunk
        overlap_text = prev_chunk[-overlap_chars:] if len(prev_chunk) > overlap_chars else prev_chunk
        
        # Find a clean break point (word boundary) in the overlap
        space_idx = overlap_text.find(" ")
        if space_idx > 0:
            overlap_text = overlap_text[space_idx + 1:]

        # Prepend overlap
        merged = overlap_text + " " + current_chunk
        overlapped_chunks.append(merged.strip())

    # Filter out very small chunks (< 20 tokens)
    final_chunks = [c for c in overlapped_chunks if _estimate_tokens(c) >= 20]

    return final_chunks


# ── CLI test ───────────────────────────────────────────────────────
if __name__ == "__main__":
    sample = """WebBee Global is a leading ecommerce integration platform that helps businesses 
    streamline their multi-channel operations. Our platform connects with major marketplaces 
    including Amazon, eBay, Walmart, and Shopify.

    Our Auto Multi-Channel Fulfillment (MCF) solution automatically routes orders from any 
    sales channel to the optimal fulfillment center. This reduces shipping costs and delivery 
    times significantly.

    Key features include inventory synchronization, order management, shipping automation, 
    and real-time analytics. WebBee supports over 100 integrations with popular ecommerce 
    platforms and marketplaces.

    Our pricing plans are designed to scale with your business. Whether you're a startup 
    processing 100 orders per month or an enterprise handling millions, we have a plan 
    that fits your needs."""

    chunks = chunk_text(sample)
    print(f"Input text: {_estimate_tokens(sample)} estimated tokens")
    print(f"Generated {len(chunks)} chunks:\n")
    for i, chunk in enumerate(chunks):
        tokens = _estimate_tokens(chunk)
        print(f"--- Chunk {i} ({tokens} tokens) ---")
        print(chunk[:200] + "..." if len(chunk) > 200 else chunk)
        print()
