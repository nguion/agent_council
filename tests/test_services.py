# AI Generated Code by Deloitte + Cursor (BEGIN)
"""
Service-level API tests (OpenAI calls mocked).

These tests focus on verifying DB-side effects (SessionState + Session metadata)
without calling external LLM APIs.
"""

import os
import tempfile

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.web.api import app
from src.web.database import Base, SessionState, get_db
from src.web.database import Session as DBSession


@pytest.fixture(scope="session")
def temp_db_url():
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
    async def override_get_db():
        async with test_db() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    # Ensure endpoints that directly use AsyncSessionLocal are also test-isolated.
    import src.web.api as api_module

    monkeypatch.setattr(api_module, "AsyncSessionLocal", test_db)
    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_build_council_persists_state(client, test_db, monkeypatch):
    # Create session
    resp = client.post(
        "/api/sessions",
        data={"question": "Test question"},
        headers={"X-User-Id": "user@example.com"},
        files=[],
    )
    assert resp.status_code == 200
    session_id = resp.json()["session_id"]

    # Mock the LLM-heavy council builder
    stub_config = {
        "council_name": "TestCouncil",
        "strategy_summary": "Stub summary",
        "agents": [{"name": "A", "persona": "P"}],
    }

    async def fake_build_council(question, ingested_data, logger=None):
        return stub_config

    import src.web.api as api_module

    monkeypatch.setattr(api_module.AgentCouncilService, "build_council", staticmethod(fake_build_council))

    build_resp = client.post(
        f"/api/sessions/{session_id}/build_council",
        headers={"X-User-Id": "user@example.com"},
    )
    assert build_resp.status_code == 200
    assert build_resp.json() == stub_config

    # Verify DB state changes
    async with test_db() as db:
        state_row = await db.get(SessionState, session_id)
        assert state_row is not None
        state = state_row.state
        assert state.get("council_config") == stub_config
        assert state.get("current_step") == "edit"
        assert state.get("status") == "build_complete"

        sess = await db.get(DBSession, session_id)
        assert sess is not None
        assert sess.current_step == "edit"
        assert sess.status == "build_complete"


@pytest.mark.asyncio
async def test_execute_sets_status_executing(client, test_db, monkeypatch):
    # Create session
    resp = client.post(
        "/api/sessions",
        data={"question": "Test execute"},
        headers={"X-User-Id": "exec-user@example.com"},
        files=[],
    )
    assert resp.status_code == 200
    session_id = resp.json()["session_id"]

    # Provide a minimal council config so execution preconditions pass
    update_resp = client.put(
        f"/api/sessions/{session_id}/council",
        headers={"X-User-Id": "exec-user@example.com"},
        json={
            "council_name": "ExecCouncil",
            "strategy_summary": "Stub",
            "agents": [{"name": "A", "persona": "P"}],
        },
    )
    assert update_resp.status_code == 200

    # Prevent background execution from mutating state during the test.
    async def fake_execute_task(_session_id: str):
        return None

    import src.web.api as api_module

    monkeypatch.setattr(api_module, "execute_council_task", fake_execute_task)

    exec_resp = client.post(
        f"/api/sessions/{session_id}/execute",
        headers={"X-User-Id": "exec-user@example.com"},
    )
    assert exec_resp.status_code == 200
    assert exec_resp.json().get("status") in {"accepted", "already_executed"}

    async with test_db() as db:
        state_row = await db.get(SessionState, session_id)
        assert state_row is not None
        state = state_row.state
        assert state.get("current_step") == "execute"
        assert state.get("status") == "executing"

# AI Generated Code by Deloitte + Cursor (END)

