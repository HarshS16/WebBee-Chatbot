"""
Playwright-based recursive web crawler for webbeeglobal.com.

Uses headless Chromium to handle JavaScript-rendered Webflow pages.
Performs BFS traversal starting from a seed URL, collecting all
internal pages up to a configurable maximum.
"""

import asyncio
import hashlib
import json
import logging
import os
import re
import sys
from datetime import datetime, timezone
from urllib.parse import urljoin, urlparse

from dotenv import load_dotenv
from playwright.async_api import async_playwright

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# ── Configuration ──────────────────────────────────────────────────
MAX_PAGES = int(os.getenv("MAX_PAGES", 500))
CRAWL_DELAY_MS = int(os.getenv("CRAWL_DELAY_MS", 500))
BASE_URL = os.getenv("BASE_URL", "https://www.webbeeglobal.com/")
BASE_DOMAIN = urlparse(BASE_URL).netloc  # e.g. "www.webbeeglobal.com"

EXCLUDE_PATTERNS = [
    "/cdn-cgi/",
    "javascript:",
    "mailto:",
    "tel:",
    "#",
    ".pdf",
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".svg",
    ".webp",
    ".mp4",
    ".zip",
    ".ico",
]

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "crawl_data")


def _normalize_url(url: str) -> str:
    """Remove fragments and trailing slashes for deduplication."""
    parsed = urlparse(url)
    # Remove fragment
    clean = parsed._replace(fragment="")
    normalized = clean.geturl().rstrip("/")
    return normalized


def _is_valid_url(url: str) -> bool:
    """Check if a URL should be crawled."""
    parsed = urlparse(url)

    # Must be same domain
    if parsed.netloc and parsed.netloc != BASE_DOMAIN:
        return False

    # Must be http(s)
    if parsed.scheme and parsed.scheme not in ("http", "https", ""):
        return False

    # Check exclude patterns
    url_lower = url.lower()
    for pattern in EXCLUDE_PATTERNS:
        if pattern in url_lower:
            return False

    return True


async def crawl(seed_url: str = BASE_URL, max_pages: int = MAX_PAGES) -> list[dict]:
    """
    BFS crawl starting from seed_url.
    
    Returns a list of dicts: {url, html, scraped_at}
    """
    visited = set()
    queue = [_normalize_url(seed_url)]
    results = []
    errors = []

    logger.info(f"Starting crawl from {seed_url}")
    logger.info(f"Max pages: {max_pages}, Crawl delay: {CRAWL_DELAY_MS}ms")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/125.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1920, "height": 1080},
        )

        page = await context.new_page()

        while queue and len(results) < max_pages:
            current_url = queue.pop(0)

            if current_url in visited:
                continue
            visited.add(current_url)

            try:
                logger.info(
                    f"[{len(results)+1}/{max_pages}] Crawling: {current_url}"
                )
                
                # Navigate and wait for network idle
                response = await page.goto(
                    current_url,
                    wait_until="networkidle",
                    timeout=30000,
                )

                if response is None or response.status >= 400:
                    status = response.status if response else "No response"
                    logger.warning(f"  ✗ HTTP {status} — skipping")
                    errors.append({"url": current_url, "error": f"HTTP {status}"})
                    continue

                # Wait a bit for any lazy-loaded content
                await page.wait_for_timeout(500)

                # Get the full rendered HTML
                html = await page.content()
                scraped_at = datetime.now(timezone.utc).isoformat()

                results.append({
                    "url": current_url,
                    "html": html,
                    "scraped_at": scraped_at,
                })

                logger.info(f"  ✓ Scraped ({len(html)} chars)")

                # Extract all links on this page
                links = await page.eval_on_selector_all(
                    "a[href]",
                    "elements => elements.map(el => el.href)"
                )

                new_links = 0
                for link in links:
                    abs_url = urljoin(current_url, link)
                    norm_url = _normalize_url(abs_url)

                    if norm_url not in visited and _is_valid_url(norm_url):
                        queue.append(norm_url)
                        new_links += 1

                logger.info(f"  → Found {new_links} new links")

                # Respect crawl delay
                await asyncio.sleep(CRAWL_DELAY_MS / 1000)

            except Exception as e:
                logger.error(f"  ✗ Error crawling {current_url}: {e}")
                errors.append({"url": current_url, "error": str(e)})
                continue

        await browser.close()

    # ── Log summary ────────────────────────────────────────────────
    logger.info("=" * 60)
    logger.info(f"Crawl complete!")
    logger.info(f"  Pages scraped: {len(results)}")
    logger.info(f"  Errors: {len(errors)}")
    logger.info(f"  URLs visited: {len(visited)}")
    logger.info("=" * 60)

    # ── Save raw crawl data ────────────────────────────────────────
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Save metadata (without HTML to keep it readable)
    meta_path = os.path.join(OUTPUT_DIR, "crawl_metadata.json")
    meta = [{"url": r["url"], "scraped_at": r["scraped_at"], "html_length": len(r["html"])} for r in results]
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)
    logger.info(f"Saved crawl metadata to {meta_path}")

    # Save each page's HTML separately
    pages_dir = os.path.join(OUTPUT_DIR, "pages")
    os.makedirs(pages_dir, exist_ok=True)
    for r in results:
        # Create a safe filename from the URL
        url_hash = hashlib.md5(r["url"].encode()).hexdigest()[:10]
        path_part = urlparse(r["url"]).path.strip("/").replace("/", "_") or "index"
        filename = f"{path_part}_{url_hash}.html"
        filepath = os.path.join(pages_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(r["html"])

    logger.info(f"Saved {len(results)} HTML files to {pages_dir}")

    # Save errors
    if errors:
        err_path = os.path.join(OUTPUT_DIR, "crawl_errors.json")
        with open(err_path, "w", encoding="utf-8") as f:
            json.dump(errors, f, indent=2)
        logger.info(f"Saved {len(errors)} errors to {err_path}")

    return results


# ── CLI entrypoint ─────────────────────────────────────────────────
if __name__ == "__main__":
    results = asyncio.run(crawl())
    print(f"\nDone. Scraped {len(results)} pages.")
