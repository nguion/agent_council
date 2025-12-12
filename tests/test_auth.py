"""
Authentication and authorization tests.

Tests cover:
- DEV mode (X-User-Id header)
- PROD mode (JWT and trusted header)
- Header spoofing prevention
- Unauthenticated request rejection
"""
import os
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from src.web.api import app


class TestAuthDevMode:
    """Test DEV mode authentication."""

    @patch.dict(os.environ, {"AUTH_MODE": "DEV"})
    def test_dev_mode_accepts_x_user_id_header(self, client):
        """Test that DEV mode accepts X-User-Id header."""
        response = client.get(
            "/api/sessions",
            headers={"X-User-Id": "dev-user@example.com"}
        )
        assert response.status_code == 200

    @patch.dict(os.environ, {"AUTH_MODE": "DEV"})
    def test_dev_mode_defaults_to_dev_user(self, client):
        """Test that DEV mode defaults to dev-user@localhost when no header."""
        response = client.get("/api/sessions")
        # Should work with default user
        assert response.status_code == 200

    @patch.dict(os.environ, {"AUTH_MODE": "DEV"})
    def test_dev_mode_creates_user_on_first_request(self, client):
        """Test that new users are auto-provisioned in DEV mode."""
        response = client.get(
            "/api/sessions",
            headers={"X-User-Id": "new-dev-user@example.com"}
        )
        assert response.status_code == 200


class TestAuthProdMode:
    """Test PROD mode authentication."""

    @patch.dict(os.environ, {"AUTH_MODE": "PROD"}, clear=False)
    def test_prod_mode_rejects_missing_auth(self, client):
        """Test that PROD mode rejects requests without authentication."""
        response = client.get("/api/sessions")
        assert response.status_code == 401
        assert "required" in response.json()["detail"].lower()

    @patch.dict(os.environ, {"AUTH_MODE": "PROD"}, clear=False)
    def test_prod_mode_accepts_trusted_header(self, client):
        """Test that PROD mode accepts X-Authenticated-User header."""
        response = client.get(
            "/api/sessions",
            headers={"X-Authenticated-User": "prod-user@example.com"}
        )
        assert response.status_code == 200

    @patch.dict(os.environ, {
        "AUTH_MODE": "PROD",
        "AUTH_JWT_SECRET": "test-secret-key-for-testing-only",
        "AUTH_JWT_ALG": "HS256"
    }, clear=False)
    def test_prod_mode_rejects_invalid_jwt(self, client):
        """Test that PROD mode rejects invalid JWT tokens."""
        response = client.get(
            "/api/sessions",
            headers={"Authorization": "Bearer invalid.jwt.token"}
        )
        assert response.status_code == 401

    @patch.dict(os.environ, {
        "AUTH_MODE": "PROD",
        "AUTH_ALLOW_X_USER_ID_IN_PROD": "false"
    }, clear=False)
    def test_prod_mode_rejects_x_user_id_by_default(self, client):
        """Test that PROD mode rejects X-User-Id header by default."""
        response = client.get(
            "/api/sessions",
            headers={"X-User-Id": "spoofed-user@example.com"}
        )
        assert response.status_code == 401

    @patch.dict(os.environ, {
        "AUTH_MODE": "PROD",
        "AUTH_ALLOW_X_USER_ID_IN_PROD": "true"
    }, clear=False)
    def test_prod_mode_allows_x_user_id_when_enabled(self, client):
        """Test that PROD mode can allow X-User-Id if escape hatch enabled."""
        # This tests the escape hatch exists, but should be disabled in real prod
        response = client.get(
            "/api/sessions",
            headers={"X-User-Id": "escape-hatch-user@example.com"}
        )
        # Should work if escape hatch enabled (but this is a security risk)
        assert response.status_code == 200


class TestSessionIsolation:
    """Test that users can only access their own sessions."""

    def test_user_cannot_access_other_user_session(self, client, dev_auth_headers):
        """Test that accessing another user's session returns 404."""
        # Create session as user1
        response1 = client.post(
            "/api/sessions",
            data={"question": "User 1 question"},
            headers={"X-User-Id": "user1@example.com"}
        )
        assert response1.status_code == 200
        session_id = response1.json()["session_id"]

        # Try to access as user2
        response2 = client.get(
            f"/api/sessions/{session_id}/summary",
            headers={"X-User-Id": "user2@example.com"}
        )
        assert response2.status_code == 404
        assert "not found" in response2.json()["detail"].lower()

    def test_user_can_access_own_session(self, client, dev_auth_headers):
        """Test that users can access their own sessions."""
        # Create session
        response1 = client.post(
            "/api/sessions",
            data={"question": "My question"},
            headers=dev_auth_headers
        )
        assert response1.status_code == 200
        session_id = response1.json()["session_id"]

        # Access own session
        response2 = client.get(
            f"/api/sessions/{session_id}/summary",
            headers=dev_auth_headers
        )
        assert response2.status_code == 200

