# Document Q&A System

A prototype system that ingests technical manuals and maintenance documents, indexes them for semantic search, and answers questions using retrieval-augmented generation (RAG).

## Features

- 📄 **Document Ingestion**: Support for PDF, DOCX, TXT, and Markdown files
- 🔍 **Semantic Search**: Vector-based similarity search using embeddings
- 🤖 **AI-Powered Q&A**: Claude LLM integration for intelligent answers
- 💬 **Chat Interface**: Conversational interface with chat history
- 🌐 **Web UI**: Modern React-based frontend
- 🔧 **Configurable PDF Parsing**: Support for both default and advanced PDF parsers

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   React     │────▶│   FastAPI   │────▶│   ChromaDB  │
│   Frontend  │◀────│   Backend   │◀────│  (Vectors)  │
└─────────────┘     └──────┬──────┘     └─────────────┘
                           │
                    ┌──────┴──────┐
                    │   Claude    │
                    │     LLM     │
                    └─────────────┘
```

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- Anthropic API key

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/docqa.git
cd docqa
```

2. Set up the backend:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. Set up the frontend:
```bash
cd ../frontend
npm install
```

4. Configure environment variables:
```bash
cp backend/.env.example backend/.env
# Edit backend/.env and add your ANTHROPIC_API_KEY
```

### Running the Application

1. Start the backend server:
```bash
cd backend
source venv/bin/activate
uvicorn main:app --reload
```

2. Start the frontend development server:
```bash
cd frontend
npm run dev
```

3. Open your browser and navigate to `http://localhost:5173`

## Configuration

### PDF Parser Options

The system supports two PDF parsers:

**1. Default (pypdf)**
- Fast and simple
- Good for text-based PDFs
- No additional dependencies

**2. Advanced (opendataloader-pdf)**
- Better for complex layouts
- Handles tables and figures
- Requires additional installation:
  ```bash
  pip install git+https://github.com/yiliangbetter/opendataloader-pdf.git
  ```

To use the advanced parser, set in your `.env`:
```
PDF_PARSER=opendataloader
```

## API Endpoints

### Documents
- `GET /api/documents` - List all documents
- `POST /api/documents` - Upload a new document
- `GET /api/documents/{id}` - Get document details
- `DELETE /api/documents/{id}` - Delete a document
- `GET /api/documents/{id}/download` - Download original file

### Query
- `POST /api/query` - Single question → answer
- `POST /api/search` - Semantic search (no LLM)
- `POST /api/chat` - Chat with history

### System
- `GET /api/stats` - System statistics
- `GET /api/health` - Health check

## Project Structure

```
docqa/
├── backend/               # FastAPI Backend
│   ├── api/              # API routes
│   ├── core/             # Business logic
│   ├── storage/          # Data storage
│   ├── config.py         # Configuration
│   ├── main.py           # Entry point
│   └── requirements.txt
├── frontend/              # React Frontend
│   ├── src/
│   │   ├── components/   # React components
│   │   ├── pages/        # Page components
│   │   ├── services/     # API services
│   │   ├── types/        # TypeScript types
│   │   └── App.tsx
│   ├── package.json
│   └── vite.config.ts
├── data/                  # Data storage (gitignored)
└── README.md
```

## Technologies Used

### Backend
- **FastAPI**: Web framework
- **ChromaDB**: Vector database
- **Sentence Transformers**: Embeddings
- **Claude (Anthropic)**: LLM for Q&A
- **Pydantic**: Data validation

### Frontend
- **React**: UI library
- **TypeScript**: Type safety
- **Chakra UI**: Component library
- **TanStack Query**: Data fetching
- **React Router**: Navigation
- **Vite**: Build tool

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Acknowledgments

- Anthropic for the Claude API
- The ChromaDB team for the vector database
- The FastAPI team for the excellent web framework
