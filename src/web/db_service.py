"""
Database service for user and session metadata operations.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from .database import Session, User


class UserService:
    """Service for user operations."""
    
    @staticmethod
    async def get_or_create_user(
        db: AsyncSession,
        external_id: str,
        display_name: Optional[str] = None
    ) -> User:
        """
        Get or create a user by their external ID (email/UPN).
        
        Args:
            db: Database session
            external_id: Email or UPN from SSO
            display_name: Optional display name
            
        Returns:
            User object
        """
        # Try to find existing user
        result = await db.execute(
            select(User).where(User.external_id == external_id)
        )
        user = result.scalar_one_or_none()
        
        if user:
            return user
        
        # Create new user
        user = User(
            id=str(uuid.uuid4()),
            external_id=external_id,
            display_name=display_name or external_id.split('@')[0],
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        db.add(user)
        try:
            await db.flush()
            return user
        except IntegrityError:
            # Another request may have created the user concurrently; return existing
            await db.rollback()
            result = await db.execute(
                select(User).where(User.external_id == external_id)
            )
            existing = result.scalar_one_or_none()
            if existing:
                return existing
            # If still missing, re-raise so caller surfaces the error
            raise


class SessionService:
    """Service for session metadata operations."""
    
    @staticmethod
    async def create_session_metadata(
        db: AsyncSession,
        session_id: str,
        user_id: str,
        question: str
    ) -> Session:
        """
        Create a new session metadata entry.
        
        Args:
            db: Database session
            session_id: Session identifier
            user_id: User identifier
            question: User's question
            
        Returns:
            Session object
        """
        session = Session(
            id=session_id,
            user_id=user_id,
            question=question,
            current_step="build",
            status="idle",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            is_deleted=False
        )
        db.add(session)
        await db.flush()
        
        return session
    
    @staticmethod
    async def get_session(
        db: AsyncSession,
        session_id: str,
        user_id: Optional[str] = None
    ) -> Optional[Session]:
        """
        Get a session by ID, optionally filtered by user.
        
        Args:
            db: Database session
            session_id: Session identifier
            user_id: Optional user filter
            
        Returns:
            Session object or None
        """
        query = select(Session).where(Session.id == session_id)
        
        if user_id:
            query = query.where(Session.user_id == user_id)
        
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    @staticmethod
    async def list_user_sessions(
        db: AsyncSession,
        user_id: str,
        include_deleted: bool = False
    ) -> list[Session]:
        """
        List all sessions for a user.
        
        Args:
            db: Database session
            user_id: User identifier
            include_deleted: Whether to include soft-deleted sessions
            
        Returns:
            List of Session objects
        """
        query = select(Session).where(Session.user_id == user_id)
        
        if not include_deleted:
            query = query.where(not Session.is_deleted)
        
        query = query.order_by(Session.created_at.desc())
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    @staticmethod
    async def update_session_metadata(
        db: AsyncSession,
        session_id: str,
        updates: dict
    ):
        """
        Update session metadata fields.
        
        Args:
            db: Database session
            session_id: Session identifier
            updates: Dictionary of fields to update
        """
        updates["updated_at"] = datetime.now(timezone.utc)
        
        await db.execute(
            update(Session)
            .where(Session.id == session_id)
            .values(**updates)
        )
        await db.flush()
    
    @staticmethod
    async def soft_delete_session(
        db: AsyncSession,
        session_id: str,
        user_id: str
    ) -> bool:
        """
        Soft delete a session (mark as deleted).
        
        Args:
            db: Database session
            session_id: Session identifier
            user_id: User identifier (for authorization)
            
        Returns:
            True if deleted, False if not found or not owned by user
        """
        session = await SessionService.get_session(db, session_id, user_id)
        if not session:
            return False
        
        await SessionService.update_session_metadata(
            db,
            session_id,
            {"is_deleted": True}
        )
        
        return True
