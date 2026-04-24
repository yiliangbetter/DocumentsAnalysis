"""Tests for documents API routes."""
from datetime import datetime
from io import BytesIO
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from config import settings
from core.document import Document, DocumentMetadata, DocumentType, ProcessingStatus


class TestListDocuments:
    """Test cases for listing documents endpoint."""

    def test_empty_list(self, test_client):
        """Test listing documents when empty."""
        response = test_client.get("/api/documents/")

        assert response.status_code == 200
        data = response.json()
        assert data["documents"] == []
        assert data["total"] == 0

    def test_with_documents(self, test_client, sample_document):
        """Test listing documents with data."""
        mock_store = test_client.app.state.document_store
        mock_store.get_all.return_value = [sample_document]
        mock_store.count.return_value = 1

        response = test_client.get("/api/documents/")

        assert response.status_code == 200
        data = response.json()
        assert len(data["documents"]) == 1
        assert data["total"] == 1
        assert data["documents"][0]["id"] == sample_document.id

    def test_pagination(self, test_client):
        """Test document pagination."""
        mock_store = test_client.app.state.document_store
        docs = [
            Document(
                id=str(i),
                title=f"Doc {i}",
                source_path=f"/path/{i}.pdf",
                doc_type=DocumentType.PDF,
            )
            for i in range(10)
        ]

        mock_store.get_all.return_value = docs[0:5]
        mock_store.count.return_value = 10

        response = test_client.get("/api/documents/?skip=0&limit=5")

        assert response.status_code == 200
        data = response.json()
        assert len(data["documents"]) == 5
        assert data["total"] == 10

    def test_filter_by_status(self, test_client, sample_document):
        """Test filtering documents by status."""
        mock_store = test_client.app.state.document_store
        mock_store.get_all.return_value = [sample_document]
        mock_store.count.return_value = 1

        response = test_client.get("/api/documents/?status=completed")

        assert response.status_code == 200

    def test_filter_by_type(self, test_client, sample_document):
        """Test filtering documents by type."""
        mock_store = test_client.app.state.document_store
        mock_store.get_all.return_value = [sample_document]
        mock_store.count.return_value = 1

        response = test_client.get("/api/documents/?doc_type=pdf")

        assert response.status_code == 200


class TestUploadDocument:
    """Test cases for upload document endpoint."""

    def test_upload_pdf(self, test_client, sample_pdf_bytes):
        """Test uploading a PDF file."""
        files = {
            "file": ("test.pdf", BytesIO(sample_pdf_bytes), "application/pdf"),
        }

        with patch("api.documents.processor") as mock_processor:
            mock_processor.process_document.return_value = (
                Document(
                    title="Test Document",
                    source_path="test.pdf",
                    doc_type=DocumentType.PDF,
                ),
                [MagicMock()],
            )

            with patch("storage.vector_store.EmbeddingGenerator"):
                response = test_client.post("/api/documents/", files=files)
                assert response.status_code == 201

    def test_upload_no_file(self, test_client):
        """Test uploading without a file."""
        response = test_client.post("/api/documents/")

        assert response.status_code == 422  # Validation error

    def test_upload_empty_filename(self, test_client):
        """Test uploading with empty filename."""
        files = {
            "file": ("", BytesIO(b"content")),
        }

        response = test_client.post("/api/documents/", files=files)

        assert response.status_code == 422

    def test_upload_unsupported_type(self, test_client):
        """Test uploading unsupported file type."""
        files = {
            "file": ("test.xyz", BytesIO(b"content")),
        }

        response = test_client.post("/api/documents/", files=files)

        assert response.status_code == 400

    def test_upload_with_title(self, test_client, sample_pdf_bytes):
        """Test uploading with custom title."""
        files = {
            "file": ("test.pdf", BytesIO(sample_pdf_bytes), "application/pdf"),
        }
        data = {
            "title": "My Custom Title",
        }

        with patch("api.documents.processor") as mock_processor:
            mock_processor.process_document.return_value = (
                Document(
                    title="My Custom Title",
                    source_path="test.pdf",
                    doc_type=DocumentType.PDF,
                ),
                [MagicMock()],
            )

            with patch("storage.vector_store.EmbeddingGenerator"):
                response = test_client.post(
                    "/api/documents/",
                    files=files,
                    data=data,
                )
                assert response.status_code == 201


class TestGetDocument:
    """Test cases for get document endpoint."""

    def test_get_existing_document(self, test_client, sample_document):
        """Test getting an existing document."""
        mock_store = test_client.app.state.document_store
        mock_store.get.return_value = sample_document

        response = test_client.get(f"/api/documents/{sample_document.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_document.id
        assert data["title"] == sample_document.title

    def test_get_nonexistent_document(self, test_client):
        """Test getting a non-existent document."""
        mock_store = test_client.app.state.document_store
        mock_store.get.return_value = None

        response = test_client.get("/api/documents/nonexistent-id")

        assert response.status_code == 404


class TestDeleteDocument:
    """Test cases for delete document endpoint."""

    def test_delete_existing_document(self, test_client, sample_document):
        """Test deleting an existing document."""
        mock_store = test_client.app.state.document_store
        mock_vector = test_client.app.state.vector_store
        mock_store.get.return_value = sample_document
        mock_store.delete.return_value = True
        mock_vector.delete_by_document_id.return_value = 5

        response = test_client.delete(f"/api/documents/{sample_document.id}")

        assert response.status_code == 204

    def test_delete_nonexistent_document(self, test_client):
        """Test deleting a non-existent document."""
        mock_store = test_client.app.state.document_store
        mock_store.get.return_value = None

        response = test_client.delete("/api/documents/nonexistent-id")

        assert response.status_code == 404


class TestDownloadDocument:
    """Test cases for download document endpoint."""

    def test_download_existing_document(self, test_client, sample_document):
        """Test downloading an existing document."""
        mock_store = test_client.app.state.document_store
        mock_store.get.return_value = sample_document

        file_storage_path = settings.FILE_STORAGE_PATH / f"{sample_document.id}.pdf"
        file_storage_path.parent.mkdir(parents=True, exist_ok=True)
        file_storage_path.write_bytes(b"PDF content")
        try:
            response = test_client.get(f"/api/documents/{sample_document.id}/download")
            assert response.status_code == 200
        finally:
            file_storage_path.unlink(missing_ok=True)

    def test_download_nonexistent_document(self, test_client):
        """Test downloading a non-existent document."""
        mock_store = test_client.app.state.document_store
        mock_store.get.return_value = None

        response = test_client.get("/api/documents/nonexistent-id/download")

        assert response.status_code == 404
