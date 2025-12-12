"""
Session State Service for DB-backed session state management.
Replaces file-based state.json with database JSON storage.
"""

import copy
import asyncio
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import OperationalError

from .database import Session as DBSession, SessionState, AsyncSessionLocal


class DatabaseBusyError(Exception):
    """Raised when database is locked after retries."""
    pass


class SessionStateService:
    """Service for managing session state in the database."""

    # In-memory batching for progress updates (per session)
    _pending_updates: Dict[str, Dict[str, Any]] = {}
    _pending_tasks: Dict[str, asyncio.Task] = {}
    _pending_lock = asyncio.Lock()
    
    @staticmethod
    async def _retry_on_lock(func, max_attempts=20, base_delay=0.5):
        """
        Retry a database operation if it fails with 'database is locked'.
        
        Args:
            func: Async function to retry
            max_attempts: Maximum number of attempts
            base_delay: Base delay in seconds (exponential backoff)
            
        Returns:
            Result of the function
            
        Raises:
            DatabaseBusyError: If all retries fail
        """
        last_error = None
        
        for attempt in range(max_attempts):
            try:
                return await func()
            except OperationalError as e:
                if "database is locked" in str(e).lower():
                    last_error = e
                    if attempt < max_attempts - 1:
                        # Cap delay at 5 seconds to avoid extremely long waits
                        # More aggressive backoff
                        delay = min(base_delay * (1.8 ** attempt), 5.0)
                        await asyncio.sleep(delay)
                        continue
                else:
                    raise
        
        raise DatabaseBusyError(
            f"Database is temporarily busy after {max_attempts} attempts. "
            "Please retry in a few seconds."
        ) from last_error
    
    @staticmethod
    # AI Generated Code by Deloitte + Cursor (BEGIN)
    async def get_state(
        db: AsyncSession,
        session_id: str,
        user_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get the current state of a session from the database.
        
        Args:
            db: Database session
            session_id: Session identifier
            user_id: Optional user filter for authorization
            
        Returns:
            Session state dict, or None if not found
        """
        # DB-only: SessionState is the single source of truth.
        # Migration from legacy state.json is handled explicitly via scripts (not at runtime).
        state_row = await db.get(SessionState, session_id)
        if not state_row:
            return None
        return state_row.state
    # AI Generated Code by Deloitte + Cursor (END)
    
    @staticmethod
    async def init_state(
        db: AsyncSession,
        session_id: str,
        user_id: str,
        question: str,
        created_at: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Initialize state for a new session.
        
        Args:
            db: Database session
            session_id: Session identifier
            user_id: User identifier
            question: User's question
            created_at: Optional creation timestamp
            
        Returns:
            Initial state dict
        """
        if created_at is None:
            created_at = datetime.utcnow()
        
        initial_state = {
            "session_id": session_id,
            "user_id": user_id,
            "created_at": created_at.isoformat(),
            "updated_at": created_at.isoformat(),
            "current_step": "input",
            "question": question,
            "context_files": [],
            "ingested_data": [],
            "council_config": None,
            "execution_results": None,
            "peer_reviews": None,
            "aggregated_scores": None,
            "chairman_verdict": None,
            "execution_status": {},
            "review_status": {},
            "tokens": {},
            "log_file": None,
            "execution_error": None,
            "review_error": None
        }
        
        await SessionStateService._persist_state(db, session_id, initial_state)
        await SessionStateService._sync_session_metadata(db, session_id, initial_state)
        await db.flush()
        return initial_state
    
    @staticmethod
    async def update_state(
        db: AsyncSession,
        session_id: str,
        updates: Dict[str, Any],
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update specific fields in the session state with deep merge support.
        Also syncs relevant fields to Session table columns.
        
        Args:
            db: Database session
            session_id: Session identifier
            updates: Dictionary of fields to update
            user_id: Optional user filter for authorization
            
        Returns:
            Updated state dict
            
        Raises:
            ValueError: If session not found
            DatabaseBusyError: If database is locked after retries
        """
        async def _do_update():
            current_state = await SessionStateService.get_state(db, session_id, user_id)
            if current_state is None:
                raise ValueError(f"Session {session_id} not found")

            merged_state = SessionStateService._deep_merge(current_state, updates)
            merged_state["updated_at"] = datetime.utcnow().isoformat()

            await SessionStateService._persist_state(db, session_id, merged_state)
            await SessionStateService._sync_session_metadata(db, session_id, merged_state, user_id)
            await db.flush()

            return merged_state
        
        return await SessionStateService._retry_on_lock(_do_update)
    
    @staticmethod
    async def set_status(
        db: AsyncSession,
        session_id: str,
        status: str,
        current_step: Optional[str] = None,
        extra_updates: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None
    ):
        """
        Set session status and optionally current_step.
        Convenience method for background tasks and status transitions.
        
        Args:
            db: Database session
            session_id: Session identifier
            status: New status value
            current_step: Optional new current_step value
            extra_updates: Optional additional fields to update in state JSON
            user_id: Optional user filter for authorization
        """
        updates = extra_updates.copy() if extra_updates else {}
        updates["status"] = status
        
        if current_step:
            updates["current_step"] = current_step
        
        await SessionStateService.update_state(db, session_id, updates, user_id)

    # -------- Batching for progress updates --------

    @classmethod
    async def update_state_batched(
        cls,
        session_id: str,
        updates: Dict[str, Any],
        user_id: Optional[str] = None,
        delay: float = 0.35
    ):
        """
        Coalesce rapid progress updates to reduce write pressure.
        """
        async with cls._pending_lock:
            base = cls._pending_updates.get(session_id, {})
            cls._pending_updates[session_id] = cls._deep_merge(base, updates)
            if session_id not in cls._pending_tasks:
                cls._pending_tasks[session_id] = asyncio.create_task(
                    cls._flush_pending(session_id, user_id, delay)
                )

    @classmethod
    async def _flush_pending(cls, session_id: str, user_id: Optional[str], delay: float):
        await asyncio.sleep(delay)
        updates = None
        async with cls._pending_lock:
            updates = cls._pending_updates.pop(session_id, None)
            cls._pending_tasks.pop(session_id, None)

        if not updates:
            return

        try:
            async with AsyncSessionLocal() as db:
                await cls.update_state(db, session_id, updates, user_id)
                await db.commit()
        except Exception as e:
            print(f"Warning: batched update failed for {session_id}: {e}")
            # Fallback: best effort retry once without batching
            try:
                async with AsyncSessionLocal() as db:
                    await cls.update_state(db, session_id, updates, user_id)
                    await db.commit()
            except Exception as e2:
                print(f"Error: retry failed for {session_id}: {e2}")
    
    @staticmethod
    def _deep_merge(base: Dict[str, Any], updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Deep merge updates into base dictionary.
        For nested dicts, merge recursively. For other types, overwrite.
        
        Args:
            base: Base dictionary
            updates: Updates to merge in
            
        Returns:
            Merged dictionary
        """
        result = copy.deepcopy(base)
        
        for key, value in updates.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                # Recursively merge nested dicts
                result[key] = SessionStateService._deep_merge(result[key], value)
            else:
                # Overwrite for all other cases
                result[key] = copy.deepcopy(value)
        
        return result

    # -------- Internal helpers --------

    @staticmethod
    # AI Generated Code by Deloitte + Cursor (BEGIN)
    async def _persist_state(db: AsyncSession, session_id: str, state: Dict[str, Any]):
        """Upsert into SessionState (DB-only)."""
        state_row = await db.get(SessionState, session_id)
        if not state_row:
            state_row = SessionState(session_id=session_id, state=state, updated_at=datetime.utcnow())
            db.add(state_row)
        else:
            state_row.state = state
            state_row.updated_at = datetime.utcnow()
    # AI Generated Code by Deloitte + Cursor (END)

    @staticmethod
    async def _sync_session_metadata(
        db: AsyncSession,
        session_id: str,
        merged_state: Dict[str, Any],
        user_id: Optional[str] = None
    ):
        """Sync key metadata fields onto the sessions table for fast querying."""
        column_updates = {
            "updated_at": datetime.utcnow()
        }

        if "current_step" in merged_state:
            column_updates["current_step"] = merged_state["current_step"]

        if "status" in merged_state:
            column_updates["status"] = merged_state["status"]

        tokens = merged_state.get("tokens", {})
        if isinstance(tokens, dict):
            if "total_cost_usd" in tokens:
                column_updates["last_cost_usd"] = tokens["total_cost_usd"]
            if "total_tokens" in tokens:
                column_updates["last_total_tokens"] = tokens["total_tokens"]

        query = update(DBSession).where(DBSession.id == session_id)
        if user_id:
            query = query.where(DBSession.user_id == user_id)

        await db.execute(query.values(**column_updates))
    
    @staticmethod
    async def get_session_with_state(
        db: AsyncSession,
        session_id: str,
        user_id: Optional[str] = None
    ) -> Optional[DBSession]:
        """
        Get the Session object with state loaded.
        Useful when you need both the ORM object and state.
        
        Args:
            db: Database session
            session_id: Session identifier
            user_id: Optional user filter for authorization
            
        Returns:
            Session ORM object or None
        """
        query = select(DBSession).where(DBSession.id == session_id)
        
        if user_id:
            query = query.where(DBSession.user_id == user_id)
        
        result = await db.execute(query)
        return result.scalar_one_or_none()
