"""
HTML parser that extracts clean text content from raw HTML.

Strips navigation, footers, scripts, styles, and other non-content
elements. Returns clean text suitable for chunking and embedding.
"""

import re
import unicodedata
from bs4 import BeautifulSoup, Comment


# Tags to remove entirely (including their children)
REMOVE_TAGS = [
    "nav",
    "footer",
    "header",
    "script",
    "style",
    "noscript",
    "aside",
    "iframe",
    "svg",
    "form",
    "button",
]

# CSS classes/IDs commonly associated with non-content elements
REMOVE_PATTERNS = [
    "cookie",
    "banner",
    "popup",
    "modal",
    "overlay",
    "newsletter",
    "social",
    "share",
    "sidebar",
    "widget",
    "advertisement",
    "menu",
    "nav",
    "breadcrumb",
]

# Content-priority tags (extract text from these first)
CONTENT_TAGS = ["main", "article", "section", "div"]


def _remove_non_content_elements(soup: BeautifulSoup) -> None:
    """Remove non-content elements from the soup in-place."""
    # Remove specified tags
    for tag_name in REMOVE_TAGS:
        for tag in soup.find_all(tag_name):
            tag.decompose()

    # Remove HTML comments
    for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
        comment.extract()

    # Remove elements with suspicious class/id names
    # Collect elements first, then decompose to avoid tree corruption
    elements_to_remove = []
    for element in soup.find_all(True):
        try:
            classes = " ".join(element.get("class", []) or [])
            element_id = element.get("id", "") or ""
            combined = f"{classes} {element_id}".lower()
            
            for pattern in REMOVE_PATTERNS:
                if pattern in combined:
                    elements_to_remove.append(element)
                    break
        except Exception:
            continue

    for element in elements_to_remove:
        try:
            element.decompose()
        except Exception:
            pass


def _normalize_text(text: str) -> str:
    """Clean up extracted text."""
    # Normalize unicode
    text = unicodedata.normalize("NFKD", text)
    
    # Replace multiple whitespace with single space
    text = re.sub(r"[ \t]+", " ", text)
    
    # Replace 3+ newlines with 2
    text = re.sub(r"\n{3,}", "\n\n", text)
    
    # Strip lines
    lines = [line.strip() for line in text.split("\n")]
    text = "\n".join(lines)
    
    # Remove leading/trailing whitespace
    text = text.strip()
    
    return text


def parse_html(html: str, url: str) -> dict:
    """
    Parse raw HTML and extract clean text content.
    
    Args:
        html: Raw HTML string
        url: Source URL for metadata
        
    Returns:
        Dict with keys: text, page_title, url
    """
    soup = BeautifulSoup(html, "html.parser")

    # Extract page title
    title_tag = soup.find("title")
    page_title = title_tag.get_text(strip=True) if title_tag else ""

    # Also try og:title or h1
    if not page_title:
        og_title = soup.find("meta", property="og:title")
        if og_title:
            page_title = og_title.get("content", "")
    
    if not page_title:
        h1 = soup.find("h1")
        if h1:
            page_title = h1.get_text(strip=True)

    # Remove non-content elements
    _remove_non_content_elements(soup)

    # Try to extract from content-priority containers
    content_text = ""
    
    for tag_name in CONTENT_TAGS:
        containers = soup.find_all(tag_name)
        if containers:
            texts = []
            for container in containers:
                text = container.get_text(separator="\n", strip=True)
                if len(text) > 50:  # Only include substantial text blocks
                    texts.append(text)
            
            if texts:
                content_text = "\n\n".join(texts)
                break

    # Fallback: extract from body
    if not content_text or len(content_text) < 100:
        body = soup.find("body")
        if body:
            content_text = body.get_text(separator="\n", strip=True)

    # Normalize the text
    clean_text = _normalize_text(content_text)

    return {
        "text": clean_text,
        "page_title": page_title or "Untitled",
        "url": url,
    }


# ── CLI test ───────────────────────────────────────────────────────
if __name__ == "__main__":
    sample_html = """
    <html>
    <head><title>WebBee Global - Test Page</title></head>
    <body>
        <nav>Navigation links here</nav>
        <main>
            <h1>Welcome to WebBee</h1>
            <p>WebBee Global is an ecommerce integration platform.</p>
            <section>
                <h2>Our Services</h2>
                <p>We provide multi-channel fulfillment solutions.</p>
            </section>
        </main>
        <footer>Copyright 2024</footer>
    </body>
    </html>
    """
    result = parse_html(sample_html, "https://www.webbeeglobal.com/test")
    print(f"Title: {result['page_title']}")
    print(f"Text length: {len(result['text'])}")
    print(f"Text:\n{result['text']}")
