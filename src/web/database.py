"""
Database models and connection for session metadata.
"""

import os
from datetime import datetime
from typing import AsyncGenerator
from sqlalchemy import Boolean, Column, DateTime, String, Float, Integer, ForeignKey, Text, JSON, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
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
    """Initialize database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
        # Enable WAL mode for SQLite to reduce lock contention
        if _is_sqlite:
            # WAL mode allows concurrent readers and one writer
            await conn.execute(text("PRAGMA journal_mode=WAL"))
            # Increase busy timeout to 60 seconds
            await conn.execute(text("PRAGMA busy_timeout=60000"))
            # Set synchronous to NORMAL for better performance (safest is FULL, but NORMAL is usually fine)
            await conn.execute(text("PRAGMA synchronous=NORMAL"))
        elif _is_postgres:
            # Optional GIN index for JSONB queries
            try:
                await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_session_state_state_gin ON session_state USING gin (state)"))
            except Exception as e:
                # Non-fatal; continue startup
                print(f"Warning: could not create GIN index on session_state: {e}")
