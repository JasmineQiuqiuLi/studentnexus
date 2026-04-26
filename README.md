# StudentNexus

**AI-powered RAG assistant for international students navigating U.S. visa regulations.**

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green?logo=fastapi)
![React](https://img.shields.io/badge/React-19-61DAFB?logo=react&logoColor=black)
![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o--mini-412991?logo=openai)
![pgvector](https://img.shields.io/badge/pgvector-Supabase-3ECF8E?logo=supabase)

---

## Overview

International students often face confusing, contradictory information when researching F-1 visa rules, OPT/CPT authorization, STEM OPT extensions, and H-1B transitions. StudentNexus solves this by providing **grounded, citation-backed answers** sourced exclusively from official immigration documentation.

Ask a question → get a direct answer with expandable source citations → follow links to primary documents.

> **Target users:** International students on F-1 visas at U.S. universities.

---

## Demo

<!-- Add a screenshot here: ![Demo](docs/demo.png) -->

*Chat UI with expandable source citations:*

```
User:  When can I apply for OPT?

Bot:   You may apply up to 90 days before your program end date
       and no later than 60 days after graduation. [Source 1]

       ▼ Source 1 — USCIS OPT Guidelines · Eligibility Section
         "Students may file the Form I-765 up to 90 days before..."
         🔗 uscis.gov  ·  Last updated: 2024-01-15
```

---

## Key Features

- **Multi-strategy retrieval** — Switch between dense vector search, hybrid BM25+vector, or hybrid with neural reranking
- **Reciprocal Rank Fusion (RRF)** — Combines semantic and keyword signals without score calibration
- **Two-stage reranking** — Cohere Rerank v3.5 refines top-20 candidates to the most relevant top-k
- **Grounded generation** — GPT-4o-mini is forced to cite specific source IDs; uncited chunks are filtered out
- **Full provenance** — Every answer shows the source chunk text, section, URL, and last-updated date

---

## Architecture

```
┌──────────────────────────────────────────────┐
│           React Frontend  (port 5173)         │
│  App.jsx · ChatWindow · CitationAccordion     │
└───────────────────┬──────────────────────────┘
                    │  POST /ask
┌───────────────────▼──────────────────────────┐
│           FastAPI Backend  (port 8000)        │
│                                               │
│  ┌────────────────────────────────────────┐  │
│  │         GenerationPipeline             │  │
│  │  retrieve_context() → generate()       │  │
│  └──────────────┬─────────────────────────┘  │
│                 │                             │
│    ┌────────────▼──────────────┐             │
│    │       SearchPipeline      │             │
│    │  dense | hybrid | rerank  │             │
│    └──┬──────────┬─────────────┘             │
│       │          │                            │
│  ┌────▼──┐  ┌───▼────┐  ┌────────────────┐  │
│  │Dense  │  │Sparse  │  │ Cohere Reranker │  │
│  │vector │  │BM25/FTS│  │  (stage 2)     │  │
│  └───┬───┘  └───┬────┘  └────────────────┘  │
│      │          │  RRF fusion                 │
│  ┌───▼──────────▼───────────────────────┐    │
│  │   PostgreSQL + pgvector (Supabase)   │    │
│  │  chunks · embeddings · tsvector FTS  │    │
│  └──────────────────────────────────────┘    │
│                                               │
│  ┌────────────────────────────────────────┐  │
│  │           LLMClient (OpenAI)           │  │
│  │  GPT-4o-mini · JSON output · citation  │  │
│  └────────────────────────────────────────┘  │
└──────────────────────────────────────────────┘

Ingestion pipeline (offline batch):
  Downloader → Markdown extractor → Cleaner
  → Chunker → Embedder → pgvector store
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | React 19, Vite, custom CSS chat UI |
| **Backend** | FastAPI, Uvicorn, Python 3.10+ |
| **LLM** | OpenAI GPT-4o-mini |
| **Embeddings** | OpenAI text-embedding-3-small · BAAI/bge-base-en · BAAI/bge-large-en |
| **Reranking** | Cohere Rerank v3.5 |
| **Vector DB** | PostgreSQL + pgvector (Supabase) |
| **Full-text search** | PostgreSQL tsvector / GIN index |
| **Data ingestion** | BeautifulSoup4, Trafilatura, Playwright, pandas |

---

## Project Structure

```
studentnexus/
├── app/
│   ├── api/
│   │   └── main.py              # FastAPI app, /ask endpoint
│   ├── generation/
│   │   ├── generation.py        # GenerationPipeline orchestrator
│   │   ├── llm_client.py        # OpenAI chat completion
│   │   ├── prompt_builder.py    # System + user prompt templates
│   │   ├── source_formatter.py  # Citation filtering & formatting
│   │   └── schemas.py           # Pydantic request/response models
│   ├── retrieval/
│   │   ├── search_pipeline.py   # Strategy dispatcher
│   │   ├── dense.py             # pgvector cosine similarity
│   │   ├── sparse.py            # PostgreSQL full-text search
│   │   └── hybrid_retrieval.py  # RRF fusion
│   └── rerank/
│       └── reranker.py          # Cohere reranking
├── frontend/
│   └── src/
│       ├── App.jsx
│       └── components/          # Header, ChatWindow, InputBar, CitationAccordion, MessageBubble
├── ingestion/
│   ├── ingestion.py             # CLI: store_chunk / store_embeddings stages
│   ├── downloader.py
│   ├── cleaner.py
│   ├── chunk_and_metadata.py
│   ├── markdown_extractor.py
│   └── embedder/
│       ├── factory.py           # Model registry
│       ├── openai_embedder.py
│       └── local_embedder.py    # HuggingFace models
├── vectorstore/
│   └── pgvector_client.py       # PostgreSQL + pgvector operations
├── notebooks/                   # Retrieval analysis & experimentation
├── requirements.txt
└── .env                         # API keys (not committed)
```

---

## Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+
- A [Supabase](https://supabase.com) project with pgvector enabled
- API keys for OpenAI and Cohere

### Environment Variables

Create a `.env` file in the project root:

```env
OPENAI_API_KEY=sk-...
COHERE_API_KEY=...
DATABASE_URL=postgresql://postgres:[password]@[host]:5432/postgres
```

### Backend

```bash
python -m venv .venv
source .venv/Scripts/activate   # Windows bash
# source .venv/bin/activate     # macOS / Linux

pip install -r requirements.txt
uvicorn app.api.main:app --reload
# API available at http://localhost:8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
# UI available at http://localhost:5173
```

---

## API Reference

### `POST /ask`

Submit a question and receive a grounded answer with cited sources.

**Request**
```json
{
  "question": "When should I apply for OPT?",
  "strategy": "hybrid_rerank",
  "top_k": 5
}
```

| Field | Type | Default | Description |
|---|---|---|---|
| `question` | string | required | Natural language question |
| `strategy` | string | `"hybrid_rerank"` | `dense` · `hybrid` · `hybrid_rerank` |
| `top_k` | integer | `5` | Number of source chunks to return |

**Response**
```json
{
  "query": "When should I apply for OPT?",
  "strategy": "hybrid_rerank",
  "answer": "You may apply up to 90 days before your program end date...",
  "sources": [
    {
      "source_id": 1,
      "title": "OPT Guidelines",
      "section": "Eligibility",
      "chunk_text": "Students may file Form I-765 up to 90 days before...",
      "url": "https://uscis.gov/...",
      "last_edited": "2024-01-15"
    }
  ]
}
```

### `GET /health`

Returns `{"status": "ok"}` — use for uptime checks.

---

## RAG Pipeline

### Retrieval Strategies

| Strategy | Description |
|---|---|
| `dense` | Cosine similarity search over OpenAI embeddings stored in pgvector |
| `hybrid` | Dense + PostgreSQL full-text search (tsvector), fused via **Reciprocal Rank Fusion (RRF)** |
| `hybrid_rerank` | Hybrid retrieves top-20, **Cohere Rerank v3.5** scores and returns top-k |

RRF formula: `score = Σ 1 / (k + rank)` across methods (k=60), combining semantic and keyword signals without score calibration.

### Grounded Generation

1. Retrieved chunks are formatted with `[source_id]` tags
2. GPT-4o-mini is prompted to return structured JSON: `{"answer": "...", "source_ids": [1, 3]}`
3. Only chunks whose IDs appear in `source_ids` are included in the response
4. Fallback: if JSON parsing fails, the raw answer is returned without citations

---

## Ingestion Pipeline

Documents are ingested offline in two stages:

```bash
# Stage 1 — Scrape, chunk, and store text + metadata
python -m ingestion.ingestion --stage store_chunk

# Stage 2 — Generate embeddings and store in pgvector
python -m ingestion.ingestion --stage store_embeddings --model_name openai-small
# model_name options: openai-small | bge-base | bge-large
```

**Flow:** Downloader → HTML→Markdown extraction → Text cleaning → Semantic chunking → Embedding → pgvector

Each chunk stores: `text`, `title`, `section`, `source_url`, `last_edited`, `token_count`

---

## License

MIT
