#!/usr/bin/env python3
"""
Comprehensive test script for PR-5 Alembic migrations.

Tests:
1. Fresh database initialization (new DB)
2. Existing database migration (stamping)
3. API functionality after migration
4. Database operations (create/read sessions)
"""

import asyncio
import os
import shutil
import sys
import tempfile
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from src.web.database import Base, init_db, get_db, User, Session, SessionState, DATABASE_URL
from src.web.db_service import UserService, SessionService
from src.web.state_service import SessionStateService
from src.web.session_manager import SessionManager


async def test_fresh_database():
    """Test 1: Fresh database initialization with migrations."""
    print("\n" + "="*60)
    print("TEST 1: Fresh Database Initialization")
    print("="*60)
    
    # Create temporary database
    temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    temp_db.close()
    db_path = temp_db.name
    
    try:
        # Set DATABASE_URL to temp database
        original_url = os.environ.get("DATABASE_URL")
        os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{db_path}"
        
        # Re-import to pick up new URL
        import importlib
        import src.web.database as db_module
        importlib.reload(db_module)
        
        # Initialize database (should run migrations)
        await db_module.init_db()
        
        # Verify tables exist
        sync_url = f"sqlite:///{db_path}"
        from sqlalchemy import create_engine
        sync_engine = create_engine(sync_url)
        inspector = inspect(sync_engine)
        tables = inspector.get_table_names()
        
        required_tables = {"users", "sessions", "session_state"}
        assert required_tables.issubset(set(tables)), f"Missing tables. Found: {tables}"
        print(f"✓ All required tables exist: {tables}")
        
        # Verify alembic_version table exists
        assert "alembic_version" in tables, "alembic_version table missing"
        print("✓ Alembic version table exists")
        
        # Check current revision
        with sync_engine.connect() as conn:
            result = conn.execute(text("SELECT version_num FROM alembic_version"))
            version = result.scalar()
            assert version == "950bd54c7a60", f"Unexpected version: {version}"
            print(f"✓ Database at correct revision: {version}")
        
        sync_engine.dispose()
        
        # Test database operations
        engine = create_async_engine(f"sqlite+aiosqlite:///{db_path}")
        async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        
        async with async_session() as session:
            # Create a test user
            user = User(
                id="test-user-123",
                external_id="test@example.com",
                display_name="Test User"
            )
            session.add(user)
            await session.commit()
            
            # Create a test session
            test_session = Session(
                id="test-session-123",
                user_id="test-user-123",
                question="Test question?",
                current_step="input",
                status="idle"
            )
            session.add(test_session)
            await session.commit()
            
            # Create session state
            state = SessionState(
                session_id="test-session-123",
                state={"test": "data"}
            )
            session.add(state)
            await session.commit()
            
            # Verify reads work
            user_read = await session.get(User, "test-user-123")
            assert user_read is not None, "User not found"
            assert user_read.external_id == "test@example.com", "User data incorrect"
            
            session_read = await session.get(Session, "test-session-123")
            assert session_read is not None, "Session not found"
            assert session_read.question == "Test question?", "Session data incorrect"
            
            state_read = await session.get(SessionState, "test-session-123")
            assert state_read is not None, "SessionState not found"
            assert state_read.state == {"test": "data"}, "State data incorrect"
            
            print("✓ Database operations (create/read) work correctly")
        
        await engine.dispose()
        
        print("\n✅ TEST 1 PASSED: Fresh database initialization works correctly")
        return True
        
    except Exception as e:
        print(f"\n❌ TEST 1 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Restore original URL
        if original_url:
            os.environ["DATABASE_URL"] = original_url
        else:
            os.environ.pop("DATABASE_URL", None)
        
        # Cleanup
        if os.path.exists(db_path):
            os.unlink(db_path)


async def test_existing_database_stamping():
    """Test 2: Existing database (created with create_all) gets stamped."""
    print("\n" + "="*60)
    print("TEST 2: Existing Database Stamping")
    print("="*60)
    
    # Create temporary database
    temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    temp_db.close()
    db_path = temp_db.name
    
    try:
        # Set DATABASE_URL to temp database
        original_url = os.environ.get("DATABASE_URL")
        os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{db_path}"
        
        # Re-import to pick up new URL
        import importlib
        import src.web.database as db_module
        importlib.reload(db_module)
        
        # Create tables using create_all (simulating old behavior)
        engine = create_async_engine(f"sqlite+aiosqlite:///{db_path}")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        await engine.dispose()
        
        print("✓ Created database with create_all() (simulating legacy)")
        
        # Now initialize with migrations (should stamp)
        await db_module.init_db()
        
        # Verify alembic_version table exists and has correct revision
        sync_url = f"sqlite:///{db_path}"
        from sqlalchemy import create_engine
        sync_engine = create_engine(sync_url)
        inspector = inspect(sync_engine)
        tables = inspector.get_table_names()
        
        assert "alembic_version" in tables, "alembic_version table missing after stamping"
        print("✓ Alembic version table created")
        
        with sync_engine.connect() as conn:
            result = conn.execute(text("SELECT version_num FROM alembic_version"))
            version = result.scalar()
            assert version == "950bd54c7a60", f"Unexpected version: {version}"
            print(f"✓ Database stamped with correct revision: {version}")
        
        sync_engine.dispose()
        
        print("\n✅ TEST 2 PASSED: Existing database stamping works correctly")
        return True
        
    except Exception as e:
        print(f"\n❌ TEST 2 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Restore original URL
        if original_url:
            os.environ["DATABASE_URL"] = original_url
        else:
            os.environ.pop("DATABASE_URL", None)
        
        # Cleanup
        if os.path.exists(db_path):
            os.unlink(db_path)


async def test_api_functionality():
    """Test 3: API functionality after migration."""
    print("\n" + "="*60)
    print("TEST 3: API Functionality")
    print("="*60)
    
    # Create temporary database
    temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    temp_db.close()
    db_path = temp_db.name
    
    # Create temporary sessions directory
    temp_sessions = tempfile.mkdtemp()
    
    try:
        # Set DATABASE_URL to temp database
        original_url = os.environ.get("DATABASE_URL")
        os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{db_path}"
        
        # Re-import to pick up new URL
        import importlib
        import src.web.database as db_module
        importlib.reload(db_module)
        
        # Initialize database
        await db_module.init_db()
        print("✓ Database initialized")
        
        # Test db_service functions
        engine = create_async_engine(f"sqlite+aiosqlite:///{db_path}")
        async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        
        async with async_session() as session:
            # Test UserService.get_or_create_user
            user = await UserService.get_or_create_user(session, "api-test@example.com", "API Test User")
            assert user is not None, "User creation failed"
            assert user.external_id == "api-test@example.com", "User external_id incorrect"
            print(f"✓ User created: {user.id}")
            
            # Test SessionService.create_session_metadata
            session_id = SessionManager.generate_session_id()
            session_obj = await SessionService.create_session_metadata(
                session,
                session_id=session_id,
                user_id=user.id,
                question="What is the meaning of life?"
            )
            assert session_obj is not None, "Session creation failed"
            assert session_obj.question == "What is the meaning of life?", "Session question incorrect"
            assert session_obj.user_id == user.id, "Session user_id incorrect"
            print(f"✓ Session created: {session_obj.id}")
            
            # Test SessionStateService.init_state
            from datetime import datetime, timezone
            await SessionStateService.init_state(
                session,
                session_id=session_id,
                user_id=user.id,
                question="What is the meaning of life?",
                created_at=datetime.now(timezone.utc)
            )
            await session.commit()
            
            # Verify session state was created
            state = await session.get(SessionState, session_id)
            assert state is not None, "SessionState not created"
            assert isinstance(state.state, dict), "SessionState.state is not a dict"
            print("✓ SessionState created correctly")
        
        await engine.dispose()
        
        print("\n✅ TEST 3 PASSED: API functionality works correctly")
        return True
        
    except Exception as e:
        print(f"\n❌ TEST 3 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Restore original URL
        if original_url:
            os.environ["DATABASE_URL"] = original_url
        else:
            os.environ.pop("DATABASE_URL", None)
        
        # Cleanup
        if os.path.exists(db_path):
            os.unlink(db_path)
        if os.path.exists(temp_sessions):
            shutil.rmtree(temp_sessions)


async def test_migration_idempotency():
    """Test 4: Running migrations multiple times is safe."""
    print("\n" + "="*60)
    print("TEST 4: Migration Idempotency")
    print("="*60)
    
    # Create temporary database
    temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    temp_db.close()
    db_path = temp_db.name
    
    try:
        # Set DATABASE_URL to temp database
        original_url = os.environ.get("DATABASE_URL")
        os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{db_path}"
        
        # Re-import to pick up new URL
        import importlib
        import src.web.database as db_module
        importlib.reload(db_module)
        
        # Run init_db multiple times
        await db_module.init_db()
        print("✓ First init_db() call completed")
        
        await db_module.init_db()
        print("✓ Second init_db() call completed")
        
        await db_module.init_db()
        print("✓ Third init_db() call completed")
        
        # Verify database is still in correct state
        sync_url = f"sqlite:///{db_path}"
        from sqlalchemy import create_engine
        sync_engine = create_engine(sync_url)
        
        with sync_engine.connect() as conn:
            result = conn.execute(text("SELECT version_num FROM alembic_version"))
            version = result.scalar()
            assert version == "950bd54c7a60", f"Version changed unexpectedly: {version}"
            print(f"✓ Database still at correct revision: {version}")
        
        sync_engine.dispose()
        
        print("\n✅ TEST 4 PASSED: Migrations are idempotent")
        return True
        
    except Exception as e:
        print(f"\n❌ TEST 4 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Restore original URL
        if original_url:
            os.environ["DATABASE_URL"] = original_url
        else:
            os.environ.pop("DATABASE_URL", None)
        
        # Cleanup
        if os.path.exists(db_path):
            os.unlink(db_path)


async def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("PR-5 Alembic Migrations - Comprehensive Test Suite")
    print("="*60)
    
    results = []
    
    # Run all tests
    results.append(await test_fresh_database())
    results.append(await test_existing_database_stamping())
    results.append(await test_api_functionality())
    results.append(await test_migration_idempotency())
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    
    if all(results):
        print("\n🎉 ALL TESTS PASSED! PR-5 is working correctly.")
        return 0
    else:
        print("\n❌ SOME TESTS FAILED. Please review the errors above.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

