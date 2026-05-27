"""
Retriever service — handles query embedding and vector search.

Encodes the user query with the same model used during ingestion,
then queries ChromaDB for the most semantically similar chunks.
"""

import logging
import os
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Import from ingestion modules
from ingestion.embedder import embed_query
from ingestion.vector_store import query_similar, get_collection

# ── Configuration ──────────────────────────────────────────────────
TOP_K = int(os.getenv("TOP_K", 5))
SIMILARITY_THRESHOLD = float(os.getenv("SIMILARITY_THRESHOLD", 0.35))
# ChromaDB uses distance (lower = better), so threshold = 1 - similarity
DISTANCE_THRESHOLD = 1 - SIMILARITY_THRESHOLD


def retrieve(query: str, top_k: int = TOP_K) -> list[dict]:
    """
    Retrieve the most relevant chunks for a query.
    
    Args:
        query: User's question
        top_k: Number of results to retrieve
        
    Returns:
        List of dicts: {text, source_url, page_title, score, chunk_index}
        Only includes results above the similarity threshold.
    """
    logger.info(f"Retrieving for query: '{query[:80]}...'")

    # Step 1: Embed the query
    query_embedding = embed_query(query)

    # Step 2: Search ChromaDB
    results = query_similar(
        query_embedding=query_embedding,
        n_results=top_k,
        distance_threshold=DISTANCE_THRESHOLD,
    )

    if results:
        logger.info(f"Found {len(results)} relevant chunks:")
        for r in results:
            logger.info(f"  Score: {r['score']:.4f} | {r['page_title'][:40]} | {r['source_url']}")
    else:
        logger.info("No chunks found above similarity threshold")

    return results
