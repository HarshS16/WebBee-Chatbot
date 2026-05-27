"""
Embedding wrapper using sentence-transformers.

Uses the all-MiniLM-L6-v2 model for generating 384-dimensional
embeddings. Supports batch encoding for efficiency.
"""

import logging
import os
from functools import lru_cache

from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

load_dotenv()

logger = logging.getLogger(__name__)

# ── Configuration ──────────────────────────────────────────────────
# Resolve the local model folder (backend/model) relative to this file
DEFAULT_MODEL_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "model"))
if os.path.exists(DEFAULT_MODEL_PATH):
    MODEL_NAME = os.getenv("EMBEDDING_MODEL", DEFAULT_MODEL_PATH)
else:
    MODEL_NAME = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
BATCH_SIZE = 64


@lru_cache(maxsize=1)
def get_model() -> SentenceTransformer:
    """Load and cache the sentence-transformer model (singleton)."""
    logger.info(f"Loading embedding model: {MODEL_NAME}")
    model = SentenceTransformer(MODEL_NAME)
    logger.info(f"Model loaded. Embedding dimension: {model.get_sentence_embedding_dimension()}")
    return model


def embed_texts(texts: list[str], batch_size: int = BATCH_SIZE, show_progress: bool = True) -> list[list[float]]:
    """
    Generate embeddings for a list of texts.
    
    Args:
        texts: List of text strings to embed
        batch_size: Batch size for encoding (default 64)
        show_progress: Show progress bar during encoding
        
    Returns:
        List of embedding vectors (each is a list of floats)
    """
    model = get_model()
    
    logger.info(f"Embedding {len(texts)} texts (batch_size={batch_size})")
    
    embeddings = model.encode(
        texts,
        batch_size=batch_size,
        show_progress_bar=show_progress,
        convert_to_numpy=True,
    )
    
    # Convert numpy arrays to lists for JSON serialization
    result = [emb.tolist() for emb in embeddings]
    
    logger.info(f"Generated {len(result)} embeddings of dimension {len(result[0])}")
    return result


def embed_query(query: str) -> list[float]:
    """
    Generate embedding for a single query string.
    
    Args:
        query: Query text to embed
        
    Returns:
        Embedding vector as a list of floats
    """
    model = get_model()
    embedding = model.encode(query, convert_to_numpy=True)
    return embedding.tolist()


# ── CLI test ───────────────────────────────────────────────────────
if __name__ == "__main__":
    texts = [
        "WebBee Global is an ecommerce integration platform.",
        "Amazon MCF fulfillment automation services.",
        "Multi-channel order management solutions.",
    ]
    
    embeddings = embed_texts(texts, show_progress=False)
    print(f"Generated {len(embeddings)} embeddings")
    print(f"Embedding dimension: {len(embeddings[0])}")
    
    query_emb = embed_query("What does WebBee do?")
    print(f"Query embedding dimension: {len(query_emb)}")
