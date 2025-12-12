"""
Shared pytest fixtures for Agent Council tests.
"""
import os
import tempfile
from typing import Generator

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.web.api import app
from src.web.database import Base, get_db


@pytest.fixture(scope="session")
def temp_db_url():
    """Create a temporary database URL for test session."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    url = f"sqlite+aiosqlite:///{path}"
    yield url
    try:
        os.remove(path)
    except FileNotFoundError:
        pass


@pytest_asyncio.fixture
async def test_db(temp_db_url):
    """Create a test database session factory."""
    engine = create_async_engine(
        temp_db_url,
        echo=False,
        future=True,
        connect_args={"timeout": 30, "check_same_thread": False},
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    yield SessionLocal
    await engine.dispose()


@pytest.fixture
def client(test_db, monkeypatch):
    """Create a test client with database dependency override."""
    async def override_get_db():
        async with test_db() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    # Patch endpoints that use AsyncSessionLocal directly
    import src.web.api as api_module
    monkeypatch.setattr(api_module, "AsyncSessionLocal", test_db)
    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


@pytest.fixture
def dev_auth_headers():
    """Headers for DEV mode authentication."""
    return {"X-User-Id": "test-user@example.com"}


@pytest.fixture
def mock_jwt_token():
    """Generate a mock JWT token for testing (not cryptographically valid)."""
    # This is a placeholder - real JWT tests will use python-jose
    return "mock.jwt.token.here"


@pytest.fixture
def sample_file_content():
    """Sample file content for upload tests."""
    return b"This is a test file content for upload testing."


@pytest.fixture
def sample_pdf_content():
    """Sample PDF content (minimal valid PDF)."""
    # Minimal valid PDF structure
    return b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\nxref\n0 0\ntrailer\n<< /Root 1 0 R >>\n%%EOF"

