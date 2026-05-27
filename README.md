# WebBee Global — RAG-Based Website Chatbot

A **Retrieval-Augmented Generation (RAG)** chatbot that answers questions exclusively using content scraped from [webbeeglobal.com](https://www.webbeeglobal.com/). Every answer is grounded in retrieved content with source citations — no hallucination allowed.

![Architecture](https://img.shields.io/badge/Architecture-RAG-blue)
![LLM](https://img.shields.io/badge/LLM-Groq%20LLaMA%203.3-green)
![Vector%20DB](https://img.shields.io/badge/VectorDB-ChromaDB-orange)
![Frontend](https://img.shields.io/badge/Frontend-React%20%2B%20Vite-purple)

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────┐
│              INGESTION PIPELINE (offline)                │
│  Playwright Crawler → BeautifulSoup Parser → Chunker     │
│  → Sentence-Transformers Embedder → ChromaDB Store       │
└──────────────────────────────────────────────────────────┘
                          │
                          ▼
┌──────────────────────────────────────────────────────────┐
│                  BACKEND API (FastAPI)                    │
│  /api/chat → Retriever → Prompt Builder → Groq LLM      │
└──────────────────────────────────────────────────────────┘
                          │
                          ▼
┌──────────────────────────────────────────────────────────┐
│                FRONTEND (React + Vite)                    │
│  Chat UI → Message Bubbles → Source Citation Cards        │
└──────────────────────────────────────────────────────────┘
```

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **LLM** | Groq — `llama-3.3-70b-versatile` (free tier) |
| **Embeddings** | `all-MiniLM-L6-v2` via sentence-transformers (local, free) |
| **Vector DB** | ChromaDB (embedded, persistent) |
| **Crawler** | Playwright (headless Chromium) |
| **HTML Parser** | BeautifulSoup4 |
| **Backend** | FastAPI + Uvicorn |
| **Frontend** | React 18 + Vite 5 + TailwindCSS 3 |

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- A free [Groq API key](https://console.groq.com/)

### 1. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate    # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Install Playwright browser
playwright install chromium

# Configure environment
# Edit .env and set your GROQ_API_KEY
```

### 2. Run Ingestion (First Time)

```bash
cd backend

# Crawl webbeeglobal.com and build the vector database
python -m ingestion.ingest

# (Optional) With flags:
python -m ingestion.ingest --max-pages 100 --clear
```

This will:
- Crawl ~200-500 pages from webbeeglobal.com
- Parse and extract clean text content
- Chunk text into ~500-token segments with overlap
- Generate embeddings using all-MiniLM-L6-v2
- Store everything in ChromaDB

**Estimated time:** 20-40 minutes (dominated by Playwright rendering)

### 3. Start Backend API

```bash
cd backend
uvicorn api.main:app --reload --port 8000
```

API docs available at: `http://localhost:8000/docs`

### 4. Start Frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173` in your browser.

---

## 📁 Project Structure

```
WebBee-Chatbot/
├── backend/
│   ├── ingestion/
│   │   ├── crawler.py          # Playwright recursive web crawler
│   │   ├── parser.py           # HTML → clean text (BeautifulSoup)
│   │   ├── chunker.py          # Token-aware text splitter
│   │   ├── embedder.py         # sentence-transformers wrapper
│   │   ├── vector_store.py     # ChromaDB interface
│   │   └── ingest.py           # Ingestion orchestrator
│   ├── api/
│   │   ├── main.py             # FastAPI app with CORS & rate limiting
│   │   ├── routers/
│   │   │   └── chat.py         # POST /api/chat endpoint
│   │   ├── services/
│   │   │   ├── retriever.py    # Query embedding + vector search
│   │   │   ├── prompt_builder.py  # Context + system prompt assembly
│   │   │   └── groq_client.py  # Groq API wrapper
│   │   └── models/
│   │       └── schemas.py      # Pydantic request/response models
│   ├── chroma_db/              # ChromaDB persistent storage
│   ├── .env                    # Environment variables
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ChatWindow.jsx  # Main chat container
│   │   │   ├── MessageBubble.jsx # User/assistant message display
│   │   │   ├── SourceCard.jsx  # Source citation card
│   │   │   └── InputBar.jsx    # Chat input with send button
│   │   ├── hooks/
│   │   │   └── useChat.js      # Chat state management hook
│   │   └── api/
│   │       └── chatApi.js      # Axios API client
│   └── ...
└── README.md
```

---

## 🔌 API Endpoints

### `POST /api/chat`
Send a message and get a RAG-grounded response.

```json
// Request
{ "message": "What integrations does WebBee support?" }

// Response
{
  "answer": "WebBee supports integrations with...",
  "sources": [
    {
      "title": "Amazon MCF Integration",
      "url": "https://www.webbeeglobal.com/auto-multi-channel-fulfillment",
      "snippet": "First 150 chars..."
    }
  ],
  "found_context": true
}
```

### `GET /api/health`
Health check with database stats.

### `POST /api/ingest`
Admin-only re-ingestion trigger (requires `X-Admin-Key` header).

---

## ⚙️ Configuration

All settings are in `backend/.env`:

| Variable | Default | Description |
|---|---|---|
| `GROQ_API_KEY` | — | Your Groq API key (required) |
| `GROQ_MODEL` | `llama-3.3-70b-versatile` | Groq model to use |
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | Sentence-transformer model |
| `MAX_PAGES` | `500` | Max pages to crawl |
| `TOP_K` | `5` | Number of chunks to retrieve |
| `SIMILARITY_THRESHOLD` | `0.35` | Minimum cosine similarity |
| `MAX_REQUESTS_PER_MINUTE` | `5` | Rate limit per IP |

---

## 🛡️ Safety & Anti-Hallucination

- **System prompt** strictly instructs the LLM to only use provided context
- **Similarity threshold** (0.35) filters out irrelevant chunks
- **No-context fallback** — graceful "I couldn't find that" response
- **Temperature 0.1** — near-deterministic output
- **Source citations** on every response for verifiability
- **Rate limiting** — 5 requests/minute per IP
- **CORS** restricted to known origins

---

## 📜 License

MIT
