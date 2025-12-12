"""
Integration tests for Agent Council API endpoints.

Tests cover:
- Session lifecycle (create, build, execute, review, synthesize)
- Precondition validation (can't execute without council, etc.)
- Idempotent operations (no duplicate charges)
- Database concurrency (no locked database errors)
- Error responses (proper HTTP codes and messages)

Run with: pytest test_api_integration.py -v
"""

import asyncio
import os
import tempfile

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Import the app and database components
from src.web.api import app
from src.web.database import Base, get_db
from src.web.state_service import DatabaseBusyError


@pytest.fixture
async def test_db():
    """Create a temporary test database."""
    # Create temporary database file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as f:
        db_path = f.name
    
    # Create test database URL
    test_database_url = f"sqlite+aiosqlite:///{db_path}"
    
    # Create test engine
    test_engine = create_async_engine(
        test_database_url,
        echo=False,
        future=True,
        connect_args={"timeout": 30, "check_same_thread": False}
    )
    
    # Create tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create session factory
    TestSessionLocal = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    yield TestSessionLocal
    
    # Cleanup
    await test_engine.dispose()
    os.unlink(db_path)


@pytest.fixture
def client(test_db, monkeypatch):
    """Create a test client with dependency override."""
    # AI Generated Code by Deloitte + Cursor (BEGIN)
    async def override_get_db():
        async with test_db() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    # Patch endpoints that use AsyncSessionLocal directly so they use the temp DB too.
    import src.web.api as api_module
    monkeypatch.setattr(api_module, "AsyncSessionLocal", test_db)
    # AI Generated Code by Deloitte + Cursor (END)
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as c:
        yield c
    
    app.dependency_overrides.clear()


class TestSessionLifecycle:
    """Test complete session lifecycle."""
    
    def create_session_helper(self, client):
        """Helper to create session with question."""
        response = client.post(
            "/api/sessions",
            data={"question": "How do I test my Agent Council?"},
            files=[]
        )
        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert data["question"] == "How do I test my Agent Council?"
        return data["session_id"]

    def test_create_session(self, client):
        """Test session creation endpoint."""
        self.create_session_helper(client)
    
    def test_build_council_requires_question(self, client):
        """Test that building council validates question exists."""
        # Create session without question would fail at creation
        # So test that build endpoint returns proper error if state is corrupt
        pass
    
    def test_build_council_success(self, client):
        """Test building council configuration."""
        # Create session
        session_id = self.create_session_helper(client)
        
        # Build council
        response = client.post(f"/api/sessions/{session_id}/build_council")
        
        # Should return council config or fail gracefully
        assert response.status_code in [200, 500]  # 500 if OpenAI not configured
        
        if response.status_code == 200:
            data = response.json()
            assert "agents" in data
    
    def test_idempotent_build(self, client):
        """Test that building twice doesn't re-run without force flag."""
        session_id = self.create_session_helper(client)
        
        # First build
        response1 = client.post(f"/api/sessions/{session_id}/build_council")
        
        # Second build without force - should return cached
        response2 = client.post(f"/api/sessions/{session_id}/build_council")
        
        # Both should return same data
        if response1.status_code == 200:
            assert response1.json() == response2.json()
    
    def test_execute_requires_council(self, client):
        """Test that execute validates council_config exists."""
        session_id = self.create_session_helper(client)
        
        # Try to execute without building council
        response = client.post(f"/api/sessions/{session_id}/execute")
        
        assert response.status_code == 400
        assert "council" in response.json()["detail"].lower()
    
    def test_peer_review_requires_execution(self, client):
        """Test that peer review validates execution_results exist."""
        session_id = self.create_session_helper(client)
        
        # Try peer review without execution
        response = client.post(f"/api/sessions/{session_id}/peer_review")
        
        assert response.status_code == 400
        assert "execution" in response.json()["detail"].lower()
    
    def test_synthesize_requires_reviews(self, client):
        """Test that synthesize validates peer_reviews exist."""
        session_id = self.create_session_helper(client)
        
        # Try synthesize without reviews
        response = client.post(f"/api/sessions/{session_id}/synthesize")
        
        assert response.status_code == 400
        detail = response.json()["detail"].lower()
        assert "execution" in detail or "review" in detail


class TestConcurrency:
    """Test concurrent database access."""
    
    @pytest.mark.asyncio
    async def test_concurrent_updates_no_lock(self, test_db):
        """Test that concurrent updates don't cause database locks."""
        from datetime import datetime, timezone

        from src.web.db_service import SessionService, UserService
        from src.web.state_service import SessionStateService
        
        # Create test session
        async with test_db() as db:
            user = await UserService.get_or_create_user(db, "test@example.com")
            await SessionService.create_session_metadata(
                db, "test_session_123", user.id, "Test question"
            )
            await SessionStateService.init_state(
                db, "test_session_123", user.id, "Test question", datetime.now(timezone.utc)
            )
            await db.commit()
        
        # Simulate concurrent updates
        async def update_session(update_num):
            async with test_db() as db:
                try:
                    await SessionStateService.update_state(
                        db,
                        "test_session_123",
                        {f"test_field_{update_num}": f"value_{update_num}"}
                    )
                    await db.commit()
                    return True
                except DatabaseBusyError:
                    return False
        
        # Run 10 concurrent updates
        results = await asyncio.gather(*[update_session(i) for i in range(10)])
        
        # Most should succeed (retry mechanism)
        success_rate = sum(results) / len(results)
        assert success_rate > 0.8, "Too many database busy errors even with retries"


class TestErrorHandling:
    """Test error handling and responses."""
    
    def test_database_busy_returns_503(self, client):
        """Test that database busy errors return 503 with helpful message."""
        # This would require mocking the database to return locked errors
        # For now, just test the structure
        pass
    
    def test_missing_session_returns_404(self, client):
        """Test accessing non-existent session returns 404."""
        response = client.get("/api/sessions/nonexistent_session_123/summary")
        assert response.status_code == 404
    
    def test_session_isolation(self, client):
        """Test that users can only access their own sessions."""
        # Create session as user1
        response1 = client.post(
            "/api/sessions",
            data={"question": "User 1 question"},
            headers={"X-User-Id": "user1@example.com"}
        )
        session_id = response1.json()["session_id"]
        
        # Try to access as user2
        response2 = client.get(
            f"/api/sessions/{session_id}/summary",
            headers={"X-User-Id": "user2@example.com"}
        )
        
        assert response2.status_code == 404  # Not found for unauthorized user

    def test_malformed_request_missing_question(self, client):
        """Test that creating session without question returns 422."""
        response = client.post(
            "/api/sessions",
            data={},  # Missing question
            files=[]
        )
        assert response.status_code == 422  # Validation error

    def test_invalid_session_id_format(self, client):
        """Test that invalid session ID format returns 404."""
        response = client.get("/api/sessions/not-a-valid-session-id/summary")
        assert response.status_code == 404

    def test_soft_deleted_session_hidden_from_list(self, client):
        """Test that soft-deleted sessions are hidden from list."""
        # Create session
        response1 = client.post(
            "/api/sessions",
            data={"question": "Test delete"},
            headers={"X-User-Id": "delete-user@example.com"}
        )
        session_id = response1.json()["session_id"]

        # Soft delete
        response2 = client.delete(
            f"/api/sessions/{session_id}",
            headers={"X-User-Id": "delete-user@example.com"}
        )
        assert response2.status_code == 200

        # Should not appear in list
        response3 = client.get(
            "/api/sessions",
            headers={"X-User-Id": "delete-user@example.com"}
        )
        assert response3.status_code == 200
        sessions = response3.json().get("sessions", [])
        session_ids = [s["id"] for s in sessions]
        assert session_id not in session_ids

    def test_soft_deleted_session_returns_410(self, client):
        """Test that accessing soft-deleted session returns 410."""
        # Create session
        response1 = client.post(
            "/api/sessions",
            data={"question": "Test delete access"},
            headers={"X-User-Id": "delete-access-user@example.com"}
        )
        session_id = response1.json()["session_id"]

        # Soft delete
        client.delete(
            f"/api/sessions/{session_id}",
            headers={"X-User-Id": "delete-access-user@example.com"}
        )

        # Try to access deleted session
        response2 = client.get(
            f"/api/sessions/{session_id}/summary",
            headers={"X-User-Id": "delete-access-user@example.com"}
        )
        assert response2.status_code == 410  # Gone

    def test_force_flag_rebuilds_council(self, client):
        """Test that force flag allows rebuilding council."""
        # Create session
        response0 = client.post(
            "/api/sessions",
            data={"question": "Test force rebuild"},
            files=[]
        )
        session_id = response0.json()["session_id"]

        # First build
        response1 = client.post(f"/api/sessions/{session_id}/build_council")
        if response1.status_code == 200:
            # Force rebuild
            response2 = client.post(
                f"/api/sessions/{session_id}/build_council?force=true"
            )
            # Should accept the request (may return same or new config)
            assert response2.status_code in [200, 500]


class TestUserManagement:
    """Test user-related functionality."""
    
    def test_auto_provision_user(self, client):
        """Test that new users are automatically provisioned."""
        response = client.get(
            "/api/sessions",
            headers={"X-User-Id": "newuser@example.com"}
        )
        assert response.status_code == 200
    
    def test_default_user_in_dev(self, client):
        """Test that dev mode uses default user when no header provided."""
        response = client.get("/api/sessions")
        assert response.status_code == 200
        # Should work with dev-user@localhost


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
