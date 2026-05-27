"""
Pydantic request/response models for the chat API.
"""

from pydantic import BaseModel, Field
from typing import Optional


class ChatRequest(BaseModel):
    """Request body for POST /api/chat."""
    message: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="User's question or message",
    )
    session_id: Optional[str] = Field(
        None,
        description="Optional session ID for future multi-turn tracking",
    )


class SourceInfo(BaseModel):
    """A single source citation."""
    title: str = Field(..., description="Page title of the source")
    url: str = Field(..., description="URL of the source page")
    snippet: str = Field(..., description="Text snippet from the matched chunk")


class ChatResponse(BaseModel):
    """Response body for POST /api/chat."""
    answer: str = Field(..., description="LLM-generated answer")
    sources: list[SourceInfo] = Field(
        default_factory=list,
        description="Source citations used to generate the answer",
    )
    found_context: bool = Field(
        ...,
        description="Whether relevant context was found in the knowledge base",
    )


class HealthResponse(BaseModel):
    """Response body for GET /api/health."""
    model_config = {'protected_namespaces': ()}

    status: str = "ok"
    chunks_in_db: int = 0
    model_loaded: bool = False


class IngestRequest(BaseModel):
    """Request body for POST /api/ingest."""
    seed_url: Optional[str] = Field(
        None,
        description="Override seed URL for crawling",
    )
    max_pages: Optional[int] = Field(
        None,
        ge=1,
        le=1000,
        description="Override max pages to crawl",
    )
    clear_existing: bool = Field(
        False,
        description="Clear existing data before re-ingesting",
    )


class IngestResponse(BaseModel):
    """Response body for POST /api/ingest."""
    status: str
    pages_crawled: int = 0
    chunks_stored: int = 0
    elapsed_seconds: float = 0
    errors: list[str] = Field(default_factory=list)


class ErrorResponse(BaseModel):
    """Generic error response."""
    error: str
    detail: Optional[str] = None
