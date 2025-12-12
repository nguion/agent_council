"""
Database models and connection for session metadata.
"""

import os
from collections.abc import AsyncGenerator
from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    pool,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base, relationship

# Database URL - use SQLite for dev, PostgreSQL for production
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./agent_council.db")

# Determine DB flavor
_is_sqlite = DATABASE_URL.startswith("sqlite")
_is_postgres = DATABASE_URL.startswith("postgres")

# Exported flags
IS_SQLITE = _is_sqlite
IS_POSTGRES = _is_postgres

# Engine kwargs
_engine_kwargs = dict(echo=False, future=True)

# Connection/pool tuning
if not _is_sqlite:
    # Modest defaults suitable for ~10–20 concurrent connections
    _engine_kwargs.update(
        pool_size=int(os.getenv("DB_POOL_SIZE", "10")),
        max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "20"))
    )

# Create async engine with appropriate config
if _is_sqlite:
    _engine_kwargs["connect_args"] = {
        "timeout": 30,
        "check_same_thread": False
    }

engine = create_async_engine(DATABASE_URL, **_engine_kwargs)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

Base = declarative_base()


class User(Base):
    """User model for tracking who owns sessions."""
    __tablename__ = "users"
    
    id = Column(String, primary_key=True)  # Internal UUID
    external_id = Column(String, unique=True, nullable=False, index=True)  # Email/UPN from SSO
    display_name = Column(String, nullable=True)
    # AI Generated Code by Deloitte + Cursor (BEGIN)
    role = Column(String, nullable=False, default="user", index=True)  # RBAC role: 'user', 'admin', 'auditor'
    # AI Generated Code by Deloitte + Cursor (END)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationship
    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")


class Session(Base):
    """Session metadata model."""
    __tablename__ = "sessions"
    
    id = Column(String, primary_key=True)  # session_id from SessionManager
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    question = Column(Text, nullable=False)
    current_step = Column(String, nullable=False, default="input")
    status = Column(String, nullable=False, default="idle")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    
    # Optional metadata
    last_cost_usd = Column(Float, nullable=True)
    last_total_tokens = Column(Integer, nullable=True)
    
    # Relationship
    user = relationship("User", back_populates="sessions")


def _state_json_type():
    """Return JSON column type appropriate for the backend."""
    if _is_postgres:
        return JSONB
    return JSON


class SessionState(Base):
    """Primary store for session state (JSON/JSONB)."""
    __tablename__ = "session_state"

    session_id = Column(String, primary_key=True)
    state = Column(_state_json_type(), nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency to get async database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """Initialize database tables using Alembic migrations."""
    # AI Generated Code by Deloitte + Cursor (BEGIN)
    from alembic.config import Config
    from alembic import command
    from alembic.runtime.migration import MigrationContext
    from sqlalchemy import create_engine, inspect
    
    # Convert async URL to sync for Alembic
    sync_url = DATABASE_URL
    if sync_url.startswith("sqlite+aiosqlite"):
        sync_url = sync_url.replace("sqlite+aiosqlite", "sqlite")
    elif sync_url.startswith("postgresql+asyncpg"):
        sync_url = sync_url.replace("postgresql+asyncpg", "postgresql")
    
    # Create sync engine for Alembic
    connect_args = {}
    if _is_sqlite:
        connect_args = {"timeout": 30, "check_same_thread": False}
    
    sync_engine = create_engine(
        sync_url,
        poolclass=pool.NullPool,
        connect_args=connect_args,
        echo=False
    )
    
    # Load Alembic config
    alembic_cfg = Config("alembic.ini")
    
    try:
        with sync_engine.connect() as connection:
            # Check if database has tables but no Alembic version (legacy create_all() DB)
            inspector = inspect(sync_engine)
            tables = inspector.get_table_names()
            has_tables = len(tables) > 0
            
            context = MigrationContext.configure(connection)
            current_rev = context.get_current_revision()
            
            # If tables exist but no revision, stamp with head (assumes schema matches)
            if has_tables and current_rev is None:
                # Check if core tables exist (users, sessions, session_state)
                required_tables = {"users", "sessions", "session_state"}
                if required_tables.issubset(set(tables)):
                    # Stamp database as being at head revision
                    alembic_cfg.attributes["connection"] = connection
                    command.stamp(alembic_cfg, "head")
                    print("Stamped existing database with current Alembic revision")
                else:
                    # Schema mismatch - run migrations
                    alembic_cfg.attributes["connection"] = connection
                    command.upgrade(alembic_cfg, "head")
                    print("Database migrated to latest schema")
            else:
                # Normal migration path
                alembic_cfg.attributes["connection"] = connection
                command.upgrade(alembic_cfg, "head")
                if current_rev:
                    print(f"Database migrated from {current_rev} to head")
                else:
                    print("Database migrations completed successfully")
    except Exception as e:
        print(f"Warning: Alembic migration failed: {e}")
        # Fallback for dev: ensure tables exist
        # In production, migrations should always succeed
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            print("Warning: Fell back to create_all() due to migration failure")
    finally:
        sync_engine.dispose()
    # AI Generated Code by Deloitte + Cursor (END)
