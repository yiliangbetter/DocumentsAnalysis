# DocumentsAnalysis

A **document Q&A** web application: upload technical manuals and other files, index them with embeddings, and ask questions using **retrieval-augmented generation (RAG)** with **Anthropic Claude**.

**Status:** v1.0-style application stack; **automated tests are not included yet** (see git tag `v1.0.0`).

## Features

- **Ingestion** — PDF, DOCX, TXT, and Markdown; configurable PDF backend (`pypdf` or optional advanced parser)
- **Semantic search** — ChromaDB + sentence-transformers embeddings
- **Q&A and chat** — Claude answers with retrieved context and citations
- **Web UI** — React (Vite, TypeScript, Chakra UI): dashboard, document manager, chat
- **REST API** — FastAPI with OpenAPI docs at `/docs`

## Architecture

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ React (Vite) │────▶│   FastAPI    │────▶│   ChromaDB   │
│   frontend   │◀────│   backend    │◀────│   (vectors)  │
└──────────────┘     └──────┬───────┘     └──────────────┘
                           │
                    ┌──────▼───────┐
                    │ Anthropic    │
                    │ Claude API   │
                    └──────────────┘
```

Local data lives under `backend/data/` (vector DB, document metadata, uploaded files). Add `data/` to backups; it is typically gitignored.

## Prerequisites

- **Python** 3.10+
- **Node.js** 18+
- **Anthropic API key** ([Anthropic Console](https://console.anthropic.com/))

## Quick start

### 1. Backend

From the repository root:

```bash
cd backend
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Create `backend/.env` (minimal example):

```env
ANTHROPIC_API_KEY=sk-ant-api03-...
```

Optional settings (see `backend/config.py`): `HOST`, `PORT`, `LLM_MODEL`, `EMBEDDING_MODEL`, `PDF_PARSER`, `CORS_ORIGINS`, paths under `./data`, etc.

Run the API (from `backend/`):

```bash
uvicorn main:app --reload
```

- API base: `http://localhost:8000`
- Interactive docs: `http://localhost:8000/docs`
- Health: `http://localhost:8000/health` or `http://localhost:8000/api/health`

### 2. Frontend

```bash
cd frontend
npm install
```

Optional: `frontend/.env` with `VITE_API_URL=http://localhost:8000` (defaults to that if unset).

```bash
npm run dev
```

Open **http://localhost:5173**.

### 3. End-to-end flow

1. Upload documents (**Documents** in the UI or `POST /api/documents/`).
2. Wait until processing completes.
3. Use **Chat** or the query API to ask questions grounded in your files.

More step-by-step detail: **[QUICKSTART.md](QUICKSTART.md)**.

## Configuration highlights

| Area | Notes |
|------|--------|
| **LLM** | `ANTHROPIC_API_KEY` required for query/chat. `LLM_MODEL` defaults in `config.py`. |
| **Embeddings** | Default `sentence-transformers/all-MiniLM-L6-v2` (downloads on first use). |
| **PDF** | `PDF_PARSER=pypdf` (default) or `opendataloader` if you install the extra dependency (see `DESIGN.md`). |
| **CORS** | `CORS_ORIGINS` must include your frontend origin (e.g. `http://localhost:5173`). |

## API overview

| Method | Path | Purpose |
|--------|------|--------|
| GET | `/health` | Simple health check (includes doc/chunk counts when stores are up) |
| GET | `/api/health` | API health JSON |
| GET | `/api/stats` | Document and chunk statistics |
| GET | `/api/documents/` | List documents |
| POST | `/api/documents/` | Upload a document (`multipart/form-data`, field `file`) |
| GET | `/api/documents/{id}` | Document detail |
| DELETE | `/api/documents/{id}` | Remove document and vectors |
| GET | `/api/documents/{id}/download` | Download original file |
| POST | `/api/query` | Single question → answer (RAG) |
| POST | `/api/search` | Semantic search only (no LLM) |
| POST | `/api/chat` | Chat message with optional history (RAG) |

Full request/response shapes: **http://localhost:8000/docs** (when the backend is running).

## Repository layout

```
DocumentsAnalysis/
├── README.md                 # This file
├── QUICKSTART.md             # Short runbook
├── DESIGN.md                 # Design and architecture notes
├── PROJECT.md                # Implementation notes and roadmap-style detail
├── backend/
│   ├── main.py               # FastAPI app
│   ├── config.py             # Settings (env)
│   ├── api/                  # documents, query, system routes
│   ├── core/                 # document models, processor, RAG
│   ├── storage/              # document store, vector store
│   └── requirements.txt
└── frontend/
    ├── src/
    │   ├── pages/            # Dashboard, DocumentManager, ChatInterface
    │   ├── components/
    │   ├── services/api.ts
    │   └── types/
    ├── vite.config.ts
    └── package.json
```

## Tech stack

| Layer | Technologies |
|-------|----------------|
| Backend | FastAPI, Pydantic Settings, ChromaDB, sentence-transformers, Anthropic SDK, pypdf / python-docx, etc. |
| Frontend | React 18, TypeScript, Vite, Chakra UI, TanStack Query, Axios, React Router |

## Documentation

- **[QUICKSTART.md](QUICKSTART.md)** — install, run, curl examples  
- **[DESIGN.md](DESIGN.md)** — product and technical design  
- **[PROJECT.md](PROJECT.md)** — structure reference and phased checklist  

## Contributing

Issues and pull requests are welcome. Please keep changes focused and consistent with existing patterns in `backend/` and `frontend/`.
