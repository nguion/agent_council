"""
Session Manager Module.
Handles file-based persistence of session state for the web application.
"""

import os
import json
import uuid
import shutil
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path


class SessionManager:
    """Manages session persistence using file-based storage."""
    
    def __init__(self, sessions_dir: str = "sessions"):
        """
        Initialize the SessionManager.
        
        Args:
            sessions_dir: Base directory for storing session data
        """
        self.sessions_dir = Path(sessions_dir)
        self.sessions_dir.mkdir(exist_ok=True)
    
    def _get_session_dir(self, session_id: str) -> Path:
        """Get the directory path for a session."""
        return self.sessions_dir / session_id
    
    def _get_state_file(self, session_id: str) -> Path:
        """Get the state.json file path for a session."""
        return self._get_session_dir(session_id) / "state.json"
    
    def _get_uploads_dir(self, session_id: str) -> Path:
        """Get the uploads directory for a session."""
        return self._get_session_dir(session_id) / "uploaded_files"
    
    def create_session(self, question: str) -> str:
        """
        Create a new session.
        
        Args:
            question: The user's initial question
            
        Returns:
            session_id: Unique identifier for the session
        """
        session_id = f"session_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
        session_dir = self._get_session_dir(session_id)
        session_dir.mkdir(parents=True, exist_ok=True)
        
        # Create uploads directory
        uploads_dir = self._get_uploads_dir(session_id)
        uploads_dir.mkdir(exist_ok=True)
        
        # Initialize state
        initial_state = {
            "session_id": session_id,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "current_step": "input",
            "question": question,
            "context_files": [],
            "ingested_data": [],
            "council_config": None,
            "execution_results": None,
            "peer_reviews": None,
            "chairman_verdict": None,
            "execution_status": {},
            "review_status": {},
            "tokens": {},
            "log_file": None
        }
        
        self._save_state(session_id, initial_state)
        return session_id
    
    def session_exists(self, session_id: str) -> bool:
        """Check if a session exists."""
        return self._get_session_dir(session_id).exists()
    
    def get_state(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the current state of a session.
        
        Args:
            session_id: The session identifier
            
        Returns:
            The session state dict, or None if not found
        """
        state_file = self._get_state_file(session_id)
        if not state_file.exists():
            return None
        
        try:
            with open(state_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading state for session {session_id}: {e}")
            return None
    
    def _save_state(self, session_id: str, state: Dict[str, Any]):
        """Save the session state."""
        state["updated_at"] = datetime.utcnow().isoformat()
        state_file = self._get_state_file(session_id)
        
        try:
            with open(state_file, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            print(f"Error saving state for session {session_id}: {e}")
            raise
    
    def update_state(self, session_id: str, updates: Dict[str, Any]):
        """
        Update specific fields in the session state.
        
        Args:
            session_id: The session identifier
            updates: Dictionary of fields to update
        """
        state = self.get_state(session_id)
        if state is None:
            raise ValueError(f"Session {session_id} not found")
        
        state.update(updates)
        self._save_state(session_id, state)
    
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
        """Delete a session and all its data."""
        session_dir = self._get_session_dir(session_id)
        if session_dir.exists():
            shutil.rmtree(session_dir)
    
    def list_sessions(self) -> List[Dict[str, Any]]:
        """
        List all sessions with basic metadata.
        
        Returns:
            List of dicts with session info
        """
        sessions = []
        for session_dir in self.sessions_dir.iterdir():
            if session_dir.is_dir():
                state = self.get_state(session_dir.name)
                if state:
                    sessions.append({
                        "session_id": state["session_id"],
                        "created_at": state["created_at"],
                        "updated_at": state["updated_at"],
                        "current_step": state.get("current_step", "unknown"),
                        "question": state.get("question", "")[:100]  # Truncate for listing
                    })
        
        # Sort by creation time, newest first
        sessions.sort(key=lambda x: x["created_at"], reverse=True)
        return sessions
