"""
Ingestion orchestrator — coordinates the full pipeline:
  crawl → parse → chunk → embed → store

This module can be run standalone or triggered via the API.
"""

import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime, timezone

from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

from ingestion.crawler import crawl
from ingestion.parser import parse_html
from ingestion.chunker import chunk_text
from ingestion.embedder import embed_texts
from ingestion.vector_store import upsert_chunks, get_collection, get_collection_stats, clear_collection


async def run_ingestion(
    seed_url: str = None,
    max_pages: int = None,
    clear_existing: bool = False,
    skip_crawl: bool = False,
) -> dict:
    """
    Run the full ingestion pipeline.
    
    Args:
        seed_url: Starting URL (defaults to env BASE_URL)
        max_pages: Max pages to crawl (defaults to env MAX_PAGES)
        clear_existing: If True, clear existing collection before ingesting
        skip_crawl: If True, skip crawling and load pages from local disk
        
    Returns:
        Dict with ingestion statistics
    """
    start_time = time.time()
    stats = {
        "started_at": datetime.now(timezone.utc).isoformat(),
        "pages_crawled": 0,
        "pages_parsed": 0,
        "total_chunks": 0,
        "chunks_embedded": 0,
        "chunks_stored": 0,
        "errors": [],
    }

    # ── Step 0: Optionally clear existing data ─────────────────────
    if clear_existing:
        logger.info("Clearing existing collection...")
        clear_collection()

    # ── Step 1: Crawl ──────────────────────────────────────────────
    logger.info("=" * 60)
    logger.info("STEP 1: CRAWLING")
    logger.info("=" * 60)

    if skip_crawl:
        logger.info("Skipping crawl, loading from disk...")
        import hashlib
        from urllib.parse import urlparse
        meta_path = os.path.join(os.path.dirname(__file__), "..", "crawl_data", "crawl_metadata.json")
        pages_dir = os.path.join(os.path.dirname(__file__), "..", "crawl_data", "pages")
        
        crawled_pages = []
        if os.path.exists(meta_path):
            with open(meta_path, "r", encoding="utf-8") as f:
                metadata = json.load(f)
            
            for meta in metadata:
                url_hash = hashlib.md5(meta["url"].encode()).hexdigest()[:10]
                path_part = urlparse(meta["url"]).path.strip("/").replace("/", "_") or "index"
                filename = f"{path_part}_{url_hash}.html"
                filepath = os.path.join(pages_dir, filename)
                
                if os.path.exists(filepath):
                    with open(filepath, "r", encoding="utf-8") as f:
                        html = f.read()
                    crawled_pages.append({
                        "url": meta["url"],
                        "html": html,
                        "scraped_at": meta["scraped_at"]
                    })
    else:
        crawl_kwargs = {}
        if seed_url:
            crawl_kwargs["seed_url"] = seed_url
        if max_pages:
            crawl_kwargs["max_pages"] = max_pages

        crawled_pages = await crawl(**crawl_kwargs)
        
    stats["pages_crawled"] = len(crawled_pages)

    if not crawled_pages:
        logger.error("No pages were crawled! Aborting.")
        stats["errors"].append("No pages crawled")
        return stats

    # ── Step 2: Parse ──────────────────────────────────────────────
    logger.info("=" * 60)
    logger.info("STEP 2: PARSING HTML")
    logger.info("=" * 60)

    parsed_pages = []
    for page in crawled_pages:
        try:
            parsed = parse_html(page["html"], page["url"])
            if parsed["text"] and len(parsed["text"]) > 50:
                parsed["scraped_at"] = page["scraped_at"]
                parsed_pages.append(parsed)
                logger.info(f"  [OK] Parsed: {parsed['page_title'][:60]} ({len(parsed['text'])} chars)")
            else:
                logger.warning(f"  [SKIP] Skipping (too little text): {page['url']}")
        except Exception as e:
            logger.error(f"  [FAIL] Parse error for {page['url']}: {e}")
            stats["errors"].append(f"Parse error: {page['url']} — {str(e)}")

    stats["pages_parsed"] = len(parsed_pages)
    logger.info(f"Parsed {len(parsed_pages)} pages with substantial content")

    if not parsed_pages:
        logger.error("No pages produced content after parsing! Aborting.")
        stats["errors"].append("No content after parsing")
        return stats

    # ── Step 3: Chunk ──────────────────────────────────────────────
    logger.info("=" * 60)
    logger.info("STEP 3: CHUNKING TEXT")
    logger.info("=" * 60)

    all_chunks = []
    all_metadatas = []

    for page in parsed_pages:
        chunks = chunk_text(page["text"])
        
        for i, chunk in enumerate(chunks):
            all_chunks.append(chunk)
            all_metadatas.append({
                "source_url": page["url"],
                "page_title": page["page_title"],
                "chunk_index": i,
                "scraped_at": page["scraped_at"],
            })

        logger.info(f"  {page['page_title'][:50]}: {len(chunks)} chunks")

    stats["total_chunks"] = len(all_chunks)
    logger.info(f"Total chunks: {len(all_chunks)}")

    # ── Step 4: Embed ──────────────────────────────────────────────
    logger.info("=" * 60)
    logger.info("STEP 4: GENERATING EMBEDDINGS")
    logger.info("=" * 60)

    embeddings = embed_texts(all_chunks)
    stats["chunks_embedded"] = len(embeddings)
    logger.info(f"Generated {len(embeddings)} embeddings")

    # ── Step 5: Store ──────────────────────────────────────────────
    logger.info("=" * 60)
    logger.info("STEP 5: STORING IN CHROMADB")
    logger.info("=" * 60)

    collection = get_collection()
    stored = upsert_chunks(all_chunks, embeddings, all_metadatas, collection)
    stats["chunks_stored"] = stored

    # ── Summary ────────────────────────────────────────────────────
    elapsed = round(time.time() - start_time, 1)
    stats["elapsed_seconds"] = elapsed
    stats["completed_at"] = datetime.now(timezone.utc).isoformat()

    # Get final collection stats
    final_stats = get_collection_stats()
    stats["collection_total"] = final_stats["total_chunks"]

    logger.info("=" * 60)
    logger.info("INGESTION COMPLETE")
    logger.info("=" * 60)
    logger.info(f"  Pages crawled:    {stats['pages_crawled']}")
    logger.info(f"  Pages parsed:     {stats['pages_parsed']}")
    logger.info(f"  Chunks created:   {stats['total_chunks']}")
    logger.info(f"  Chunks embedded:  {stats['chunks_embedded']}")
    logger.info(f"  Chunks stored:    {stats['chunks_stored']}")
    logger.info(f"  Total in DB:      {stats['collection_total']}")
    logger.info(f"  Errors:           {len(stats['errors'])}")
    logger.info(f"  Time elapsed:     {elapsed}s")
    logger.info("=" * 60)

    # Save stats to file
    stats_path = os.path.join(os.path.dirname(__file__), "..", "crawl_data", "ingestion_stats.json")
    os.makedirs(os.path.dirname(stats_path), exist_ok=True)
    with open(stats_path, "w") as f:
        json.dump(stats, f, indent=2)
    logger.info(f"Stats saved to {stats_path}")

    return stats


# ── CLI entrypoint ─────────────────────────────────────────────────
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run the WebBee ingestion pipeline")
    parser.add_argument("--url", type=str, help="Seed URL to crawl from")
    parser.add_argument("--max-pages", type=int, help="Maximum pages to crawl")
    parser.add_argument("--clear", action="store_true", help="Clear existing data before ingesting")
    parser.add_argument("--skip-crawl", action="store_true", help="Skip crawling and use local data")
    
    args = parser.parse_args()

    result = asyncio.run(run_ingestion(
        seed_url=args.url,
        max_pages=args.max_pages,
        clear_existing=args.clear,
        skip_crawl=args.skip_crawl,
    ))

    print(f"\nIngestion finished. {result['chunks_stored']} chunks stored in {result.get('elapsed_seconds', '?')}s")
