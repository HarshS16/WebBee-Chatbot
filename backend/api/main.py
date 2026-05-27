"""
FastAPI application entrypoint.

Configures the app with CORS, rate limiting, routers, and
health/admin endpoints.
"""

import asyncio
import logging
import os
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone

from dotenv import load_dotenv
from fastapi import FastAPI, Request, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# ── Configuration ──────────────────────────────────────────────────
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:3000").split(",")
MAX_REQUESTS_PER_MINUTE = int(os.getenv("MAX_REQUESTS_PER_MINUTE", 5))
ADMIN_API_KEY = os.getenv("ADMIN_API_KEY", "")

# ── App setup ──────────────────────────────────────────────────────
app = FastAPI(
    title="WebBee Chatbot API",
    description="RAG-based chatbot for webbeeglobal.com",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Simple in-memory rate limiter ──────────────────────────────────
rate_limit_store: dict[str, list[float]] = defaultdict(list)


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Token-bucket rate limiter per IP address."""
    # Only rate limit the chat endpoint
    if request.url.path == "/api/chat" and request.method == "POST":
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        window = 60  # 1 minute window

        # Clean old entries
        rate_limit_store[client_ip] = [
            t for t in rate_limit_store[client_ip] if now - t < window
        ]

        if len(rate_limit_store[client_ip]) >= MAX_REQUESTS_PER_MINUTE:
            logger.warning(f"Rate limit exceeded for {client_ip}")
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded",
                    "detail": f"Maximum {MAX_REQUESTS_PER_MINUTE} requests per minute. Please wait and try again.",
                },
            )

        rate_limit_store[client_ip].append(now)

    response = await call_next(request)
    return response


# ── Import and include routers ─────────────────────────────────────
from api.routers.chat import router as chat_router

app.include_router(chat_router)


# ── Health endpoint ────────────────────────────────────────────────
@app.get("/api/health")
async def health():
    """Health check endpoint with DB stats."""
    try:
        from ingestion.vector_store import get_collection_stats
        stats = get_collection_stats()
        
        model_loaded = False
        try:
            from ingestion.embedder import get_model
            get_model()
            model_loaded = True
        except Exception:
            pass

        return {
            "status": "ok",
            "chunks_in_db": stats.get("total_chunks", 0),
            "model_loaded": model_loaded,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return {
            "status": "degraded",
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


# ── Admin: Trigger ingestion ──────────────────────────────────────
@app.post("/api/ingest")
async def trigger_ingestion(
    x_admin_key: str = Header(None, alias="X-Admin-Key"),
):
    """
    Trigger a re-ingestion of the website.
    Protected by X-Admin-Key header.
    """
    # Validate admin key
    if not ADMIN_API_KEY or ADMIN_API_KEY == "your_admin_secret_key_here":
        raise HTTPException(
            status_code=503,
            detail="Admin API key is not configured. Set ADMIN_API_KEY in .env",
        )

    if x_admin_key != ADMIN_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid admin key")

    logger.info("Admin triggered re-ingestion")

    try:
        from ingestion.ingest import run_ingestion
        
        # Run ingestion in background
        result = await run_ingestion(clear_existing=True)

        return {
            "status": "completed",
            "pages_crawled": result.get("pages_crawled", 0),
            "chunks_stored": result.get("chunks_stored", 0),
            "elapsed_seconds": result.get("elapsed_seconds", 0),
            "errors": result.get("errors", []),
        }
    except Exception as e:
        logger.error(f"Ingestion error: {e}")
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")


# ── Root redirect ─────────────────────────────────────────────────
@app.get("/")
async def root():
    """Root endpoint — redirect to docs."""
    return {
        "message": "WebBee Chatbot API",
        "docs": "/docs",
        "health": "/api/health",
    }
