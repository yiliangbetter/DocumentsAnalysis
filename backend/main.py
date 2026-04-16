"""FastAPI application entry point."""
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from config import settings
from storage.document_store import DocumentStore
from storage.vector_store import VectorStore


# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# Global store instances
document_store: DocumentStore = None
vector_store: VectorStore = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler - startup and shutdown."""
    global document_store, vector_store

    # Startup
    print("Starting up Document Q&A API...")
    document_store = DocumentStore()
    vector_store = VectorStore()
    print(f"Loaded {document_store.count()} documents")
    print(f"Vector store contains {vector_store.get_chunk_count()} chunks")

    yield

    # Shutdown
    print("Shutting down Document Q&A API...")


# Create FastAPI app
app = FastAPI(
    title="Document Q&A API",
    description="API for document ingestion, indexing, and question answering",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle global exceptions."""
    # Log full exception details for debugging
    logger.exception(
        "Unhandled exception during request %s %s: %s",
        request.method,
        request.url,
        exc
    )

    # Only expose details in debug mode
    if settings.DEBUG:
        return JSONResponse(
            status_code=500,
            content={"detail": str(exc), "type": type(exc).__name__},
        )

    # Production: generic error message
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "documents": document_store.count() if document_store else 0,
        "chunks": vector_store.get_chunk_count() if vector_store else 0,
    }


# Import and include API routers
from api.documents import router as documents_router
from api.query import router as query_router
from api.system import router as system_router

app.include_router(documents_router, prefix="/api/documents", tags=["documents"])
app.include_router(query_router, prefix="/api", tags=["query"])
app.include_router(system_router, prefix="/api", tags=["system"])

# Mount static files for frontend (if built)
frontend_build_dir = Path(__file__).parent / "static"
if frontend_build_dir.exists():
    app.mount("/", StaticFiles(directory=frontend_build_dir, html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
