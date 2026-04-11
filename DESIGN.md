# Technical Manual Q&A System - Design Document

## Overview
A prototype system that ingests technical manuals and maintenance documents, indexes them for semantic search, and answers questions using retrieval-augmented generation (RAG).

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Document      │────▶│   Document       │────▶│   Vector        │
│   Ingestion       │     │   Processor        │     │   Index/Store     │
│   (PDF/DOCX/TXT)  │     │   (Chunk/Embed)    │     │   (ChromaDB)      │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                                                           │
┌─────────────────┐     ┌──────────────────┐              │
│   User Query    │────▶│   Query          │──────────────┘
│   (Question)    │     │   Engine         │
└─────────────────┘     └──────────────────┘
                               │
                               ▼
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Generated     │◀────│   LLM            │◀────│   Context         │
│   Answer        │     │   (Claude API)   │     │   (Top-k Chunks)  │
└─────────────────┘     └──────────────────┘     └─────────────────┘
```

## Core Components

### 1. Document Ingestion Layer
- **Purpose**: Accept documents in various formats
- **Supported Formats**: PDF, DOCX, TXT, Markdown
- **Key Libraries**: `pypdf`, `python-docx`, `unstructured`

### 2. Document Processor
- **Text Extraction**: Extract clean text from documents
- **Metadata Extraction**: Document title, author, date, page numbers
- **Chunking Strategy**:
  - Chunk size: 512 tokens (configurable)
  - Overlap: 50 tokens between chunks
  - Preserve paragraph boundaries when possible
- **Embedding Model**: `sentence-transformers/all-MiniLM-L6-v2` (384 dimensions, fast and good quality)

### 3. Vector Store
- **Technology**: ChromaDB (embedded, no external dependencies)
- **Storage**: Local filesystem
- **Features**: Similarity search, metadata filtering
- **Index Type**: HNSW (Hierarchical Navigable Small World) for fast approximate nearest neighbor search

### 4. Query Engine
- **Query Processing**: Convert natural language questions to embeddings
- **Retrieval Strategy**:
  - Top-k retrieval (k=5 by default)
  - Similarity threshold filtering (optional)
  - Metadata filters (e.g., search only specific document types)

### 5. Answer Generation (RAG Pipeline)
- **LLM**: Claude via Anthropic API
- **Context Window**: Up to 200K tokens (more than enough for retrieved chunks)
- **Prompt Template**:
  ```
  You are a technical support assistant. Answer the question based ONLY on the provided context.
  If the context doesn't contain enough information, say "I don't have enough information to answer this."
  Cite specific document names and sections when possible.

  Context:
  {retrieved_chunks}

  Question: {user_question}

  Answer:
  ```

## Data Model

### Document
```python
class Document:
    id: str  # UUID
    title: str
    source_path: str
    doc_type: str  # pdf, docx, txt, etc.
    created_at: datetime
    metadata: Dict[str, Any]  # author, date, etc.
```

### DocumentChunk
```python
class DocumentChunk:
    id: str  # UUID
    document_id: str
    text: str
    chunk_index: int
    start_char: int
    end_char: int
    embedding: List[float]  # 384-dimensional vector
```

## API/Interface Design

### Command-Line Interface (CLI)
```bash
# Ingest documents
python -m docqa ingest /path/to/manuals/*.pdf

# Query
python -m docqa query "How do I reset the password on Model X?"

# List documents
python -m docqa list

# Delete document
python -m docqa delete <doc_id>
```

### Python API
```python
from docqa import DocumentQA

qa = DocumentQA()

# Ingest
qa.ingest("/path/to/manual.pdf")

# Query
response = qa.query("How do I perform maintenance?")
print(response.answer)
print(response.sources)  # Source documents
```

## Project Structure

```
docqa/
├── README.md
├── requirements.txt
├── DESIGN.md
├── config.py          # Configuration settings
├── __init__.py
├── cli.py             # Command-line interface
├── core/
│   ├── __init__.py
│   ├── document.py    # Document models
│   ├── processor.py   # Text extraction & chunking
│   ├── indexer.py     # Vector indexing
│   └── rag.py         # Retrieval + Generation
├── storage/
│   ├── __init__.py
│   ├── vector_store.py   # ChromaDB wrapper
│   └── document_store.py # Metadata storage
└── utils/
    ├── __init__.py
    └── helpers.py
```

## Implementation Phases

### Phase 1: Core Infrastructure
- [ ] Project setup (requirements, structure)
- [ ] Document models and data classes
- [ ] Configuration management

### Phase 2: Ingestion Pipeline
- [ ] Document loaders (PDF, DOCX, TXT)
- [ ] Text extraction
- [ ] Metadata extraction

### Phase 3: Processing & Indexing
- [ ] Text chunking with overlap
- [ ] Embedding generation
- [ ] ChromaDB integration
- [ ] Vector storage

### Phase 4: Query & RAG
- [ ] Similarity search
- [ ] Context assembly
- [ ] Claude API integration
- [ ] Answer generation

### Phase 5: Interface
- [ ] CLI implementation
- [ ] Python API
- [ ] Documentation

## Dependencies

```txt
# Core
pydantic>=2.0.0
python-dotenv>=1.0.0

# Document Processing
pypdf>=4.0.0
python-docx>=1.1.0
unstructured>=0.12.0

# Embeddings & Vector DB
sentence-transformers>=2.5.0
chromadb>=0.4.0

# LLM
anthropic>=0.18.0

# CLI
click>=8.1.0
rich>=13.0.0

# Utilities
tqdm>=4.66.0
```

## Configuration

Environment variables in `.env`:
```bash
# LLM Configuration
ANTHROPIC_API_KEY=your_key_here
LLM_MODEL=claude-3-sonnet-20240229

# Vector Store
VECTOR_DB_PATH=./data/vector_db

# Processing
CHUNK_SIZE=512
CHUNK_OVERLAP=50
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

# Search
TOP_K_RETRIEVAL=5
SIMILARITY_THRESHOLD=0.7
```

---

## Next Steps

1. **Review this design** - Provide feedback on architecture, features, or priorities
2. **Approve the design** - I'll proceed with Phase 1 implementation
3. **Request modifications** - Change scope, add features, or adjust priorities

What would you like to change or proceed with?
