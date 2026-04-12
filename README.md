# DocumentsAnalysis

A **document Q&A** web application: upload technical manuals and other files, index them with embeddings, and ask questions using **retrieval-augmented generation (RAG)** with a given LLM.

**Status:** The stack includes **automated tests** (backend: pytest; frontend: Vitest). The git tag **`v1.0.0`** marks an earlier snapshot from before tests were added.

## Features

- **Ingestion** — PDF, DOCX, TXT, and Markdown; configurable PDF backend (`pypdf` or optional advanced parser)
- **Semantic search** — ChromaDB + sentence-transformers embeddings
- **Q&A and chat** — Kimi K2.5 answers with retrieved context and citations
- **Web UI** — React (Vite, TypeScript, Chakra UI): dashboard, document manager, chat
- **REST API** — FastAPI with OpenAPI docs at `/docs`
- **Tests** — Pytest for the API and core modules; Vitest for frontend units (see [Testing](#testing))

## Architecture

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ React (Vite) │────▶│   FastAPI    │────▶│   ChromaDB   │
│   frontend   │◀────│   backend    │◀────│   (vectors)  │
└──────────────┘     └──────┬───────┘     └──────────────┘
                           │
                    ┌──────▼───────┐
                    │ Moonshot AI  │
                    │ Kimi K2.5 API│
                    └──────────────┘
```

Local data lives under `backend/data/` (vector DB, document metadata, uploaded files). Add `data/` to backups; it is typically gitignored.

## Prerequisites

- **Python** 3.10+
- **Node.js** 18+
- **Kimi API key** ([Moonshot AI Platform](https://platform.moonshot.cn/))

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
KIMI_API_KEY=sk-...
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

## Testing

### Backend (pytest)

From `backend/`, install app + test dependencies, then run the suite:

```bash
cd backend
source venv/bin/activate   # if using a venv
pip install -r requirements-test.txt
pytest
```

Configuration lives in [`backend/pytest.ini`](backend/pytest.ini) (verbosity, coverage report to `htmlcov/`, markers such as `unit` / `integration` / `requires_model`). Run a subset from `backend/`: `pytest tests/api/test_documents.py -v`.

### Frontend (Vitest)

From `frontend/`:

```bash
cd frontend
npm install
npm test              # watch mode
npm run test:coverage # single run with coverage
```

Config: [`frontend/vitest.config.ts`](frontend/vitest.config.ts). Example tests live under `frontend/src/**/__tests__/`.

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
│   ├── pytest.ini            # Pytest / coverage defaults
│   ├── api/                  # documents, query, system routes
│   ├── core/                 # document models, processor, RAG
│   ├── storage/              # document store, vector store
│   ├── tests/                # Pytest suites (api, core, storage, …)
│   ├── requirements.txt
│   └── requirements-test.txt # Pytest + extras (install for `pytest`)
└── frontend/
    ├── src/
    │   ├── pages/            # Dashboard, DocumentManager, ChatInterface
    │   ├── components/
    │   ├── services/api.ts
    │   ├── services/__tests__/  # Vitest examples
    │   └── types/
    ├── vite.config.ts
    ├── vitest.config.ts
    └── package.json
```

## Tech stack

| Layer | Technologies |
|-------|----------------|
| Backend | FastAPI, Pydantic Settings, ChromaDB, sentence-transformers, OpenAI SDK (for Kimi), pypdf / python-docx, etc. |
| Frontend | React 18, TypeScript, Vite, Chakra UI, TanStack Query, Axios, React Router |
| Testing | **Backend:** pytest, pytest-cov, httpx, respx (see `requirements-test.txt`). **Frontend:** Vitest, Testing Library, jsdom. |

## Documentation

- **[QUICKSTART.md](QUICKSTART.md)** — install, run, curl examples  
- **[DESIGN.md](DESIGN.md)** — product and technical design  
- **[PROJECT.md](PROJECT.md)** — structure reference and phased checklist  

## Contributing

Issues and pull requests are welcome. Please keep changes focused and consistent with existing patterns in `backend/` and `frontend/`. When you change behavior or APIs, extend or add tests and run **`pytest`** (backend) and **`npm test`** (frontend) before submitting.
