"""
ChromaDB vector store interface for storing and querying embeddings.

Provides persistent storage for document chunks with metadata,
supporting both ingestion (upsert) and retrieval (query) operations.
"""

import hashlib
import logging
import os
from datetime import datetime, timezone

import chromadb
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# ── Configuration ──────────────────────────────────────────────────
CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH", os.path.join(os.path.dirname(__file__), "..", "chroma_db"))
COLLECTION_NAME = os.getenv("CHROMA_COLLECTION_NAME", "webbeeglobal")


def get_client() -> chromadb.PersistentClient:
    """Get a persistent ChromaDB client."""
    abs_path = os.path.abspath(CHROMA_DB_PATH)
    os.makedirs(abs_path, exist_ok=True)
    logger.info(f"ChromaDB path: {abs_path}")
    return chromadb.PersistentClient(path=abs_path)


def get_collection(client: chromadb.PersistentClient = None):
    """Get or create the webbeeglobal collection."""
    if client is None:
        client = get_client()
    
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"}  # Use cosine similarity
    )
    logger.info(f"Collection '{COLLECTION_NAME}' — {collection.count()} documents")
    return collection


def generate_chunk_id(source_url: str, chunk_index: int) -> str:
    """Generate a deterministic ID for a chunk (for deduplication)."""
    raw = f"{source_url}::chunk_{chunk_index}"
    return hashlib.md5(raw.encode()).hexdigest()


def upsert_chunks(
    chunks: list[str],
    embeddings: list[list[float]],
    metadatas: list[dict],
    collection=None,
) -> int:
    """
    Upsert chunks with embeddings and metadata into ChromaDB.
    
    Args:
        chunks: List of text chunk strings
        embeddings: List of embedding vectors
        metadatas: List of metadata dicts (source_url, page_title, chunk_index, scraped_at)
        collection: ChromaDB collection (will be auto-created if None)
        
    Returns:
        Number of chunks upserted
    """
    if collection is None:
        collection = get_collection()

    if not chunks:
        logger.warning("No chunks to upsert")
        return 0

    # Generate deterministic IDs for deduplication
    ids = [
        generate_chunk_id(meta["source_url"], meta["chunk_index"])
        for meta in metadatas
    ]

    # ChromaDB has a batch limit, so we process in batches
    batch_size = 100
    total_upserted = 0

    for i in range(0, len(chunks), batch_size):
        batch_end = min(i + batch_size, len(chunks))
        
        collection.upsert(
            ids=ids[i:batch_end],
            documents=chunks[i:batch_end],
            embeddings=embeddings[i:batch_end],
            metadatas=metadatas[i:batch_end],
        )
        
        total_upserted += batch_end - i
        logger.info(f"  Upserted batch {i//batch_size + 1}: {batch_end - i} chunks")

    logger.info(f"Total upserted: {total_upserted} chunks. Collection now has {collection.count()} documents.")
    return total_upserted


def query_similar(
    query_embedding: list[float],
    n_results: int = 5,
    distance_threshold: float = 0.65,
    collection=None,
) -> list[dict]:
    """
    Query the vector store for similar chunks.
    
    Args:
        query_embedding: Query embedding vector
        n_results: Number of results to return
        distance_threshold: Maximum distance (lower = more similar).
                          0.65 distance ≈ 0.35 cosine similarity.
        collection: ChromaDB collection
        
    Returns:
        List of dicts: {text, source_url, page_title, score, chunk_index}
    """
    if collection is None:
        collection = get_collection()

    if collection.count() == 0:
        logger.warning("Collection is empty — no results")
        return []

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
        include=["documents", "metadatas", "distances"],
    )

    # Parse results
    matches = []
    
    if results and results["documents"] and results["documents"][0]:
        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        ):
            # Filter by distance threshold
            if dist <= distance_threshold:
                similarity = 1 - dist  # Convert distance to similarity
                matches.append({
                    "text": doc,
                    "source_url": meta.get("source_url", ""),
                    "page_title": meta.get("page_title", ""),
                    "score": round(similarity, 4),
                    "chunk_index": meta.get("chunk_index", 0),
                    "distance": round(dist, 4),
                })

    logger.info(f"Query returned {len(matches)} results above threshold (out of {n_results} requested)")
    return matches


def get_collection_stats() -> dict:
    """Get stats about the ChromaDB collection."""
    try:
        collection = get_collection()
        return {
            "collection_name": COLLECTION_NAME,
            "total_chunks": collection.count(),
            "db_path": os.path.abspath(CHROMA_DB_PATH),
        }
    except Exception as e:
        logger.error(f"Error getting collection stats: {e}")
        return {
            "collection_name": COLLECTION_NAME,
            "total_chunks": 0,
            "db_path": os.path.abspath(CHROMA_DB_PATH),
            "error": str(e),
        }


def clear_collection(collection=None) -> None:
    """Clear all data from the collection (use with caution)."""
    client = get_client()
    try:
        client.delete_collection(COLLECTION_NAME)
        logger.info(f"Deleted collection '{COLLECTION_NAME}'")
    except Exception:
        logger.info(f"Collection '{COLLECTION_NAME}' doesn't exist, nothing to delete")
    
    # Recreate empty collection
    get_collection(client)
    logger.info(f"Recreated empty collection '{COLLECTION_NAME}'")


# ── CLI test ───────────────────────────────────────────────────────
if __name__ == "__main__":
    stats = get_collection_stats()
    print(f"Collection stats: {stats}")
