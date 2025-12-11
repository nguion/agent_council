"""
Session Manager Module.
Handles filesystem operations for session data (uploads, logs, directories).
State management is now handled by SessionStateService (database-backed).
"""

import os
import json
import uuid
import shutil
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path


class SessionManager:
    """
    Manages session filesystem operations (uploads, logs, directories).
    
    Note: Session state is now managed by SessionStateService in the database.
    This class focuses on file artifacts like uploads and logs.
    """
    
    def __init__(self, sessions_dir: str = "sessions"):
        """
        Initialize the SessionManager.
        
        Args:
            sessions_dir: Base directory for storing session data
        """
        self.sessions_dir = Path(sessions_dir)
        self.sessions_dir.mkdir(exist_ok=True)
    
    @staticmethod
    def generate_session_id() -> str:
        """
        Generate a unique session identifier.
        
        Returns:
            Unique session ID string
        """
        return f"session_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
    
    def _get_session_dir(self, session_id: str) -> Path:
        """Get the directory path for a session."""
        return self.sessions_dir / session_id
    
    def _get_uploads_dir(self, session_id: str) -> Path:
        """Get the uploads directory for a session."""
        return self._get_session_dir(session_id) / "uploaded_files"
    
    def ensure_session_directories(self, session_id: str):
        """
        Ensure session directories exist.
        
        Args:
            session_id: Session identifier
        """
        session_dir = self._get_session_dir(session_id)
        session_dir.mkdir(parents=True, exist_ok=True)
        
        # Create uploads directory
        uploads_dir = self._get_uploads_dir(session_id)
        uploads_dir.mkdir(exist_ok=True)
    
    def session_directory_exists(self, session_id: str) -> bool:
        """Check if a session directory exists on filesystem."""
        return self._get_session_dir(session_id).exists()
    
    def save_uploaded_file(self, session_id: str, filename: str, content: bytes) -> str:
        """
        Save an uploaded file to the session's uploads directory.
        
        Args:
            session_id: The session identifier
            filename: Original filename
            content: File content as bytes
            
        Returns:
            The full path to the saved file
        """
        uploads_dir = self._get_uploads_dir(session_id)
        filepath = uploads_dir / filename
        
        try:
            with open(filepath, 'wb') as f:
                f.write(content)
            return str(filepath)
        except Exception as e:
            print(f"Error saving file {filename}: {e}")
            raise
    
    def get_uploaded_files(self, session_id: str) -> List[str]:
        """Get list of uploaded file paths for a session."""
        uploads_dir = self._get_uploads_dir(session_id)
        if not uploads_dir.exists():
            return []
        
        return [str(f) for f in uploads_dir.iterdir() if f.is_file()]
    
    def delete_session(self, session_id: str):
        """
        Delete a session's filesystem data (uploads, logs, etc.).
        Note: This does not delete database state - use SessionService for that.
        
        Args:
            session_id: Session identifier
        """
        session_dir = self._get_session_dir(session_id)
        if session_dir.exists():
            shutil.rmtree(session_dir)
    
    def get_state(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get session state from state.json file.
        Used for background tasks to avoid database lock contention.
        
        Args:
            session_id: Session identifier
            
        Returns:
            State dict or None if not found
        """
        state_file = self._get_session_dir(session_id) / "state.json"
        if not state_file.exists():
            return None
        
        try:
            with open(state_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error reading state for {session_id}: {e}")
            return None
    
    def update_state(self, session_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update session state in state.json file.
        Used for background tasks to avoid database lock contention.
        
        Args:
            session_id: Session identifier
            updates: Dictionary of fields to update
            
        Returns:
            Updated state dict
        """
        state_file = self._get_session_dir(session_id) / "state.json"
        
        # Load current state or create new
        if state_file.exists():
            with open(state_file, 'r', encoding='utf-8') as f:
                state = json.load(f)
        else:
            state = {
                "session_id": session_id,
                "created_at": datetime.utcnow().isoformat()
            }
        
        # Merge updates (deep merge for nested dicts)
        for key, value in updates.items():
            if key in state and isinstance(state[key], dict) and isinstance(value, dict):
                # Merge nested dicts
                state[key] = {**state[key], **value}
            else:
                state[key] = value
        
        state["updated_at"] = datetime.utcnow().isoformat()
        
        # Write back to file
        with open(state_file, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
        
        return state
