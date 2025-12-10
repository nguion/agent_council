"""
FastAPI Application for Agent Council Web Interface.
"""

import asyncio
import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
from pathlib import Path

from .session_manager import SessionManager
from .services import AgentCouncilService
from agent_council.utils.session_logger import SessionLogger


# Initialize FastAPI app
app = FastAPI(
    title="Agent Council API",
    description="Web API for the Agent Council system",
    version="1.0.0"
)

# CORS middleware for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # Vite default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize session manager
session_manager = SessionManager()

# Global dict to track background task progress
task_progress = {}


# Pydantic models
class SessionCreate(BaseModel):
    question: str


class CouncilConfig(BaseModel):
    council_name: Optional[str] = None
    strategy_summary: Optional[str] = None
    agents: List[dict]


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None


# Helper functions
def get_session_logger(session_id: str) -> SessionLogger:
    """Get or create a logger for the session."""
    state = session_manager.get_state(session_id)
    if not state:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    
    # Use the logs directory relative to session
    logs_dir = Path("sessions") / session_id / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    
    logger = SessionLogger(output_dir=str(logs_dir))
    
    # Save log path to state
    session_manager.update_state(session_id, {"log_file": logger.path})
    
    return logger


def progress_callback_factory(session_id: str, status_type: str):
    """Factory to create progress callbacks that update session state."""
    def callback(agent_name: str, status: str):
        if session_id not in task_progress:
            task_progress[session_id] = {}
        if status_type not in task_progress[session_id]:
            task_progress[session_id][status_type] = {}
        
        task_progress[session_id][status_type][agent_name] = status
        
        # Also update session state
        state = session_manager.get_state(session_id)
        if state:
            state_key = f"{status_type}_status"
            if state_key not in state:
                state[state_key] = {}
            state[state_key][agent_name] = status
            session_manager.update_state(session_id, {state_key: state[state_key]})
    
    return callback


# Endpoints

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Agent Council API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/api/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.post("/api/sessions")
async def create_session(
    question: str = Form(...),
    files: List[UploadFile] = File(default=[])
):
    """
    Create a new session with optional file uploads.
    
    Args:
        question: The user's core question
        files: Optional list of context files
    
    Returns:
        Session ID and context file metadata
    """
    try:
        # Create session
        session_id = session_manager.create_session(question)
        
        # Save uploaded files
        file_paths = []
        for file in files:
            content = await file.read()
            filepath = session_manager.save_uploaded_file(session_id, file.filename, content)
            file_paths.append(filepath)
        
        # Ingest files
        ingested_data = []
        context_files_meta = []
        
        if file_paths:
            ingested_data = AgentCouncilService.ingest_files(file_paths)
            context_files_meta = [
                {
                    "filename": item["metadata"]["filename"],
                    "extension": item["metadata"]["extension"],
                    "size_bytes": item["metadata"]["size_bytes"]
                }
                for item in ingested_data
            ]
        
        # Update session state
        session_manager.update_state(session_id, {
            "context_files": file_paths,
            "ingested_data": ingested_data,
            "current_step": "build"
        })
        
        return {
            "session_id": session_id,
            "question": question,
            "context_files": context_files_meta
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/sessions/{session_id}/build_council")
async def build_council(session_id: str):
    """
    Build a council configuration using the Architect agent.
    
    Args:
        session_id: The session identifier
    
    Returns:
        Council configuration
    """
    try:
        state = session_manager.get_state(session_id)
        if not state:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
        
        question = state["question"]
        ingested_data = state.get("ingested_data", [])
        
        logger = get_session_logger(session_id)
        
        council_config = await AgentCouncilService.build_council(
            question,
            ingested_data,
            logger=logger
        )
        
        # Update session state
        session_manager.update_state(session_id, {
            "council_config": council_config,
            "current_step": "edit",
            "tokens": logger.get_cost_breakdown()
        })
        
        return council_config
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/sessions/{session_id}/council")
async def update_council(session_id: str, council_config: CouncilConfig):
    """
    Update the council configuration.
    
    Args:
        session_id: The session identifier
        council_config: Updated council configuration
    
    Returns:
        Success message
    """
    try:
        state = session_manager.get_state(session_id)
        if not state:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
        
        session_manager.update_state(session_id, {
            "council_config": council_config.dict(),
            "current_step": "execute"
        })
        
        return {"status": "success", "message": "Council configuration updated"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def execute_council_task(session_id: str):
    """Background task to execute the council."""
    try:
        state = session_manager.get_state(session_id)
        council_config = state["council_config"]
        question = state["question"]
        ingested_data = state.get("ingested_data", [])
        
        logger = get_session_logger(session_id)
        
        # Initialize progress
        task_progress[session_id] = {"execution": {}}
        
        progress_cb = progress_callback_factory(session_id, "execution")
        
        execution_results = await AgentCouncilService.execute_council(
            council_config,
            question,
            ingested_data,
            progress_callback=progress_cb,
            logger=logger
        )
        
        # Update session state
        session_manager.update_state(session_id, {
            "execution_results": execution_results,
            "current_step": "review",
            "tokens": logger.get_cost_breakdown()
        })
        
    except Exception as e:
        print(f"Error in execute_council_task: {e}")
        session_manager.update_state(session_id, {
            "execution_error": str(e)
        })


@app.post("/api/sessions/{session_id}/execute")
async def execute_council(session_id: str, background_tasks: BackgroundTasks):
    """
    Execute the council in parallel (background task).
    
    Args:
        session_id: The session identifier
    
    Returns:
        Acceptance message
    """
    try:
        state = session_manager.get_state(session_id)
        if not state:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
        
        if not state.get("council_config"):
            raise HTTPException(status_code=400, detail="Council not configured")
        
        # Start background task
        background_tasks.add_task(execute_council_task, session_id)
        
        return {"status": "accepted", "message": "Execution started"}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/sessions/{session_id}/status")
async def get_status(session_id: str):
    """
    Get the current execution/review status.
    
    Args:
        session_id: The session identifier
    
    Returns:
        Status information
    """
    try:
        state = session_manager.get_state(session_id)
        if not state:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
        
        progress = task_progress.get(session_id, {})
        
        # Determine overall status
        execution_complete = state.get("execution_results") is not None
        review_complete = state.get("peer_reviews") is not None
        verdict_complete = state.get("chairman_verdict") is not None
        
        status = "idle"
        if verdict_complete:
            status = "verdict_complete"
        elif review_complete:
            status = "review_complete"
        elif execution_complete:
            status = "execution_complete"
        elif progress.get("execution"):
            status = "executing"
        elif progress.get("review"):
            status = "reviewing"
        
        return {
            "status": status,
            "current_step": state.get("current_step", "unknown"),
            "execution_status": state.get("execution_status", {}),
            "review_status": state.get("review_status", {}),
            "progress": progress
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/sessions/{session_id}/results")
async def get_results(session_id: str):
    """
    Get execution results.
    
    Args:
        session_id: The session identifier
    
    Returns:
        Execution results
    """
    try:
        state = session_manager.get_state(session_id)
        if not state:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
        
        execution_results = state.get("execution_results")
        if not execution_results:
            raise HTTPException(status_code=404, detail="Execution results not available yet")
        
        return execution_results
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def peer_review_task(session_id: str):
    """Background task to run peer review."""
    try:
        state = session_manager.get_state(session_id)
        council_config = state["council_config"]
        question = state["question"]
        execution_results = state["execution_results"]["execution_results"]
        
        logger = get_session_logger(session_id)
        
        # Initialize progress
        if session_id not in task_progress:
            task_progress[session_id] = {}
        task_progress[session_id]["review"] = {}
        
        progress_cb = progress_callback_factory(session_id, "review")
        
        peer_reviews = await AgentCouncilService.run_peer_review(
            council_config,
            question,
            execution_results,
            progress_callback=progress_cb,
            logger=logger
        )
        
        # Aggregate scores
        aggregated_scores = AgentCouncilService.aggregate_reviews(
            execution_results,
            peer_reviews
        )
        
        # Update session state
        session_manager.update_state(session_id, {
            "peer_reviews": peer_reviews,
            "aggregated_scores": aggregated_scores,
            "current_step": "synthesize",
            "tokens": logger.get_cost_breakdown()
        })
        
    except Exception as e:
        print(f"Error in peer_review_task: {e}")
        session_manager.update_state(session_id, {
            "review_error": str(e)
        })


@app.post("/api/sessions/{session_id}/peer_review")
async def peer_review(session_id: str, background_tasks: BackgroundTasks):
    """
    Run peer review process (background task).
    
    Args:
        session_id: The session identifier
    
    Returns:
        Acceptance message
    """
    try:
        state = session_manager.get_state(session_id)
        if not state:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
        
        if not state.get("execution_results"):
            raise HTTPException(status_code=400, detail="No execution results available")
        
        # Start background task
        background_tasks.add_task(peer_review_task, session_id)
        
        return {"status": "accepted", "message": "Peer review started"}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/sessions/{session_id}/reviews")
async def get_reviews(session_id: str):
    """
    Get peer review results and aggregated scores.
    
    Args:
        session_id: The session identifier
    
    Returns:
        Peer reviews and aggregated scores
    """
    try:
        state = session_manager.get_state(session_id)
        if not state:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
        
        peer_reviews = state.get("peer_reviews")
        if peer_reviews is None:
            raise HTTPException(status_code=404, detail="Peer reviews not available yet")
        
        return {
            "reviews": peer_reviews,
            "aggregated_scores": state.get("aggregated_scores", {})
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/sessions/{session_id}/synthesize")
async def synthesize(session_id: str):
    """
    Generate the Chairman's final verdict.
    
    Args:
        session_id: The session identifier
    
    Returns:
        Final verdict
    """
    try:
        state = session_manager.get_state(session_id)
        if not state:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
        
        if not state.get("execution_results") or not state.get("peer_reviews"):
            raise HTTPException(status_code=400, detail="Execution and peer review must be completed first")
        
        question = state["question"]
        execution_results = state["execution_results"]["execution_results"]
        peer_reviews = state["peer_reviews"]
        
        logger = get_session_logger(session_id)
        
        final_verdict = await AgentCouncilService.synthesize_verdict(
            question,
            execution_results,
            peer_reviews,
            logger=logger
        )
        
        # Finalize logger
        logger.finalize()
        
        # Update session state
        session_manager.update_state(session_id, {
            "chairman_verdict": final_verdict,
            "current_step": "complete",
            "tokens": logger.get_cost_breakdown()
        })
        
        return {"verdict": final_verdict}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/sessions/{session_id}/summary")
async def get_summary(session_id: str):
    """
    Get complete session summary.
    
    Args:
        session_id: The session identifier
    
    Returns:
        Complete session data
    """
    try:
        state = session_manager.get_state(session_id)
        if not state:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
        
        return {
            "session_id": session_id,
            "question": state.get("question"),
            "council_config": state.get("council_config"),
            "execution_results": state.get("execution_results"),
            "peer_reviews": state.get("peer_reviews"),
            "aggregated_scores": state.get("aggregated_scores"),
            "chairman_verdict": state.get("chairman_verdict"),
            "tokens": state.get("tokens", {}),
            "log_file": state.get("log_file"),
            "created_at": state.get("created_at"),
            "updated_at": state.get("updated_at")
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/sessions")
async def list_sessions():
    """
    List all sessions.
    
    Returns:
        List of sessions with metadata
    """
    try:
        sessions = session_manager.list_sessions()
        return {"sessions": sessions}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
