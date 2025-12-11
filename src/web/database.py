"""
Database models and connection for session metadata.
"""

import os
from datetime import datetime
from typing import AsyncGenerator
from sqlalchemy import Boolean, Column, DateTime, String, Float, Integer, ForeignKey, Text, JSON, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base, relationship

# Database URL - use SQLite for dev, PostgreSQL for production
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./agent_council.db")

# Determine if we're using SQLite
_is_sqlite = DATABASE_URL.startswith("sqlite")

# Create async engine with appropriate config
if _is_sqlite:
    # SQLite-specific configuration
    engine = create_async_engine(
        DATABASE_URL,
        echo=False,
        future=True,
        connect_args={
            "timeout": 30,  # 30 second timeout for lock waits
            "check_same_thread": False
        }
    )
else:
    # PostgreSQL or other DB
    engine = create_async_engine(
        DATABASE_URL,
        echo=False,
        future=True
    )

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
    
    # Full session state as JSON (replaces state.json files)
    state = Column(JSON, nullable=True)
    
    # Relationship
    user = relationship("User", back_populates="sessions")


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
