"""
File upload tests.

Tests cover:
- File upload acceptance
- File type validation (when PR-7 adds allow-list)
- File size limits (when PR-7 adds limits)
- DISABLE_UPLOADS kill-switch (when PR-7 adds it)
- File extraction and ingestion
"""
import io
import os
from unittest.mock import patch

import pytest
from fastapi import UploadFile


class TestFileUploads:
    """Test file upload functionality."""

    def test_upload_single_file(self, client, dev_auth_headers, sample_file_content):
        """Test uploading a single file."""
        files = [
            ("files", ("test.txt", io.BytesIO(sample_file_content), "text/plain"))
        ]
        response = client.post(
            "/api/sessions",
            data={"question": "Test with file"},
            files=files,
            headers=dev_auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert len(data.get("context_files", [])) == 1
        assert data["context_files"][0]["filename"] == "test.txt"

    def test_upload_multiple_files(self, client, dev_auth_headers, sample_file_content):
        """Test uploading multiple files."""
        files = [
            ("files", ("file1.txt", io.BytesIO(sample_file_content), "text/plain")),
            ("files", ("file2.txt", io.BytesIO(sample_file_content), "text/plain"))
        ]
        response = client.post(
            "/api/sessions",
            data={"question": "Test with multiple files"},
            files=files,
            headers=dev_auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data.get("context_files", [])) == 2

    def test_upload_empty_session(self, client, dev_auth_headers):
        """Test creating session without files."""
        response = client.post(
            "/api/sessions",
            data={"question": "Test without files"},
            files=[],
            headers=dev_auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert len(data.get("context_files", [])) == 0

    # TODO: Enable these tests when PR-7 adds file validation
    @pytest.mark.skip(reason="File type allow-list not yet implemented (PR-7)")
    def test_reject_disallowed_file_type(self, client, dev_auth_headers):
        """Test that disallowed file types are rejected."""
        # This test will be enabled when PR-7 adds allow-list
        pass

    @pytest.mark.skip(reason="File size limits not yet implemented (PR-7)")
    def test_reject_oversized_file(self, client, dev_auth_headers):
        """Test that files exceeding size limit are rejected."""
        # This test will be enabled when PR-7 adds size limits
        pass

    @pytest.mark.skip(reason="DISABLE_UPLOADS kill-switch not yet implemented (PR-7)")
    @patch.dict(os.environ, {"DISABLE_UPLOADS": "true"})
    def test_uploads_disabled_via_kill_switch(self, client, dev_auth_headers, sample_file_content):
        """Test that uploads are rejected when DISABLE_UPLOADS=true."""
        # This test will be enabled when PR-7 adds kill-switch
        files = [
            ("files", ("test.txt", io.BytesIO(sample_file_content), "text/plain"))
        ]
        response = client.post(
            "/api/sessions",
            data={"question": "Test with file"},
            files=files,
            headers=dev_auth_headers
        )
        assert response.status_code == 403  # Forbidden
        assert "upload" in response.json()["detail"].lower()

    def test_file_extraction_persists_to_state(self, client, dev_auth_headers, sample_file_content, test_db):
        """Test that uploaded file content is extracted and stored in state."""
        from src.web.database import SessionState

        files = [
            ("files", ("test.txt", io.BytesIO(sample_file_content), "text/plain"))
        ]
        response = client.post(
            "/api/sessions",
            data={"question": "Test extraction"},
            files=files,
            headers=dev_auth_headers
        )
        assert response.status_code == 200
        session_id = response.json()["session_id"]

        # Verify state contains ingested_data
        import asyncio
        async def check_state():
            async with test_db() as db:
                state_row = await db.get(SessionState, session_id)
                assert state_row is not None
                state = state_row.state
                assert "ingested_data" in state
                assert len(state["ingested_data"]) > 0
                assert state["ingested_data"][0]["metadata"]["filename"] == "test.txt"

        asyncio.run(check_state())

