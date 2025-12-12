"""
FastAPI Application for Agent Council Web Interface.
"""

import asyncio
import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import BackgroundTasks, Depends, FastAPI, File, Form, Header, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from agent_council.utils.session_logger import SessionLogger

from .database import AsyncSessionLocal, User, get_db, init_db
from .database import Session as DBSession
from .db_service import SessionService, UserService
from .services import AgentCouncilService
from .session_manager import SessionManager
from .state_service import DatabaseBusyError, SessionStateService


# Database initialization on startup
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on app startup."""
    await init_db()
    yield

# Initialize FastAPI app
app = FastAPI(
    title="Agent Council API",
    description="Web API for the Agent Council system",
    version="1.0.0",
    lifespan=lifespan
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




# AI Generated Code by Deloitte + Cursor (BEGIN)
def _get_auth_mode() -> str:
    mode = (os.getenv("AUTH_MODE") or "DEV").strip().upper()
    return mode if mode in {"DEV", "PROD"} else "DEV"


def _extract_external_id_from_bearer_token(token: str) -> str:
    """
    Decode and validate a Bearer token and extract a stable external user id.

    Supported env vars:
    - AUTH_JWT_SECRET: HS* shared secret (e.g., HS256)
    - AUTH_JWT_PUBLIC_KEY: RS* public key (e.g., RS256)
    - AUTH_JWT_ALG: algorithm override (default HS256 if secret else RS256)
    - AUTH_JWT_AUDIENCE: optional audience enforcement
    - AUTH_JWT_ISSUER: optional issuer enforcement
    """
    try:
        from jose import JWTError, jwt  # type: ignore
    except ImportError:
        raise HTTPException(
            status_code=500,
            detail="Bearer token auth requires python-jose. Install backend web deps via requirements-web.txt",
        )

    jwt_secret = os.getenv("AUTH_JWT_SECRET")
    jwt_public_key = os.getenv("AUTH_JWT_PUBLIC_KEY")
    jwt_alg = (os.getenv("AUTH_JWT_ALG") or ("HS256" if jwt_secret else "RS256")).strip()
    audience = os.getenv("AUTH_JWT_AUDIENCE")
    issuer = os.getenv("AUTH_JWT_ISSUER")

    key = jwt_secret or jwt_public_key
    if not key:
        raise HTTPException(
            status_code=500,
            detail="JWT auth misconfigured: set AUTH_JWT_SECRET or AUTH_JWT_PUBLIC_KEY",
        )

    options = {"verify_aud": bool(audience), "verify_iss": bool(issuer)}
    try:
        payload = jwt.decode(
            token,
            key,
            algorithms=[jwt_alg],
            audience=audience,
            issuer=issuer,
            options=options,
        )
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid bearer token")

    external_id = (
        payload.get("email")
        or payload.get("upn")
        or payload.get("preferred_username")
        or payload.get("sub")
    )
    if not external_id:
        raise HTTPException(status_code=401, detail="Bearer token missing user identity claim")

    return str(external_id)
# AI Generated Code by Deloitte + Cursor (END)


# User context helper
async def get_current_user(
    db: AsyncSession = Depends(get_db),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    x_authenticated_user: Optional[str] = Header(None, alias="X-Authenticated-User"),
    authorization: Optional[str] = Header(None, alias="Authorization"),
) -> User:
    """
    Get or create the current user from request headers.
    
    DEV mode:
      - Accepts `X-User-Id` (email/UPN). If missing, defaults to `dev-user@localhost`.

    PROD mode (AUTH_MODE=PROD):
      - Requires either:
        - `X-Authenticated-User` (trusted header injected by a reverse proxy / gateway), OR
        - `Authorization: Bearer <JWT>` (validated via AUTH_JWT_* env vars)
    
    Args:
        db: Database session
        x_user_id: User identifier from header
        
    Returns:
        User object
    """
    # AI Generated Code by Deloitte + Cursor (BEGIN)
    auth_mode = _get_auth_mode()

    if auth_mode == "DEV":
        user_external_id = x_user_id or "dev-user@localhost"
        if not x_user_id:
            print("Warning: AUTH_MODE=DEV and no X-User-Id provided; using dev-user@localhost")
    else:
        allow_x_user_id_in_prod = (os.getenv("AUTH_ALLOW_X_USER_ID_IN_PROD") or "false").strip().lower() in {
            "1",
            "true",
            "yes",
        }

        if x_authenticated_user:
            user_external_id = x_authenticated_user
        elif authorization and authorization.lower().startswith("bearer "):
            token = authorization.split(" ", 1)[1].strip()
            if not token:
                raise HTTPException(status_code=401, detail="Missing bearer token")
            user_external_id = _extract_external_id_from_bearer_token(token)
        elif allow_x_user_id_in_prod and x_user_id:
            user_external_id = x_user_id
        else:
            raise HTTPException(status_code=401, detail="Authentication required")

    return await UserService.get_or_create_user(db, external_id=user_external_id)
    # AI Generated Code by Deloitte + Cursor (END)


# AI Generated Code by Deloitte + Cursor (BEGIN)
def require_role(required_role: str):
    """
    FastAPI dependency factory to require a specific role.
    
    Usage:
        @app.get("/admin/endpoint")
        async def admin_endpoint(user: User = Depends(require_role("admin"))):
            ...
    
    Args:
        required_role: Required role (e.g., 'admin', 'auditor')
        
    Returns:
        Dependency function that checks role and returns User
    """
    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role != required_role:
            raise HTTPException(
                status_code=403,
                detail=f"Access denied. Required role: {required_role}, current role: {current_user.role}"
            )
        return current_user
    
    return role_checker
# AI Generated Code by Deloitte + Cursor (END)


# Pydantic models
class SessionCreate(BaseModel):
    question: str


class CouncilConfig(BaseModel):
    council_name: Optional[str] = None
    strategy_summary: Optional[str] = None
    agents: list[dict]


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None


# Helper functions
async def authorize_session_access(
    session_id: str,
    user_id: str,
    db: AsyncSession
) -> DBSession:
    """
    Authorize user access to a session.
    
    Args:
        session_id: Session identifier
        user_id: User identifier
        db: Database session
        
    Returns:
        Session object if authorized
        
    Raises:
        HTTPException: If session not found or user not authorized
    """
    db_session = await SessionService.get_session(db, session_id, user_id)
    
    if not db_session:
        raise HTTPException(
            status_code=404,
            detail=f"Session {session_id} not found or you don't have access"
        )
    
    if db_session.is_deleted:
        raise HTTPException(
            status_code=410,
            detail=f"Session {session_id} has been deleted"
        )
    
    return db_session


async def read_state_primary(
    session_id: str,
    db: AsyncSession,
    user_id: Optional[str] = None
):
    # AI Generated Code by Deloitte + Cursor (BEGIN)
    """Read session state from the database (single source of truth)."""
    return await SessionStateService.get_state(db, session_id, user_id)
    # AI Generated Code by Deloitte + Cursor (END)


async def write_state_primary(
    session_id: str,
    updates: dict,
    db: Optional[AsyncSession] = None,
    user_id: Optional[str] = None,
    batched: bool = False
):
    # AI Generated Code by Deloitte + Cursor (BEGIN)
    """Write session state to the database with optional batching."""
    if batched:
        await SessionStateService.update_state_batched(session_id, updates, user_id)
        return
    if db is None:
        raise ValueError("DB session required for direct state update")
    await SessionStateService.update_state(db, session_id, updates, user_id)
    # AI Generated Code by Deloitte + Cursor (END)


async def get_session_logger(session_id: str, db: AsyncSession, update_state: bool = True) -> SessionLogger:
    """
    Get or create a logger for the session.
    
    Args:
        session_id: Session identifier
        db: Database session
        update_state: If False, skip updating state (avoid DB contention in background tasks)
    
    Returns:
        SessionLogger instance
    """
    # Use the logs directory relative to session
    logs_dir = Path("sessions") / session_id / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    
    logger = SessionLogger(output_dir=str(logs_dir))
    
    # Optionally save log path to state in DB
    # Skip in background tasks to avoid DB lock contention
    if update_state:
        try:
            await SessionStateService.update_state(db, session_id, {"log_file": logger.path})
        except Exception as e:
            # Non-critical - log file path can be inferred
            print(f"Warning: Could not save log file path for {session_id}: {e}")
    
    return logger


# Progress callbacks are now defined inline in background tasks
# using file-based state updates (no database contention)


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


# AI Generated Code by Deloitte + Cursor (BEGIN)
@app.get("/api/admin/metrics/summary")
async def admin_metrics_summary(
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(require_role("admin"))
):
    """
    Admin-only endpoint for aggregated metrics summary.
    
    Returns placeholder metrics data. Real implementation will aggregate
    from sessions, tokens, costs, and error logs.
    
    Requires 'admin' role.
    """
    # Placeholder response - will be implemented in Sprint 2
    return {
        "total_sessions": 0,
        "active_users": 0,
        "total_tokens": 0,
        "total_cost_usd": 0.0,
        "error_rate": 0.0,
        "p50_latency_ms": 0,
        "p95_latency_ms": 0,
        "note": "Placeholder metrics - real implementation in Sprint 2"
    }
# AI Generated Code by Deloitte + Cursor (END)


@app.post("/api/sessions")
async def create_session(
    question: str = Form(...),
    files: list[UploadFile] = File(default=[]),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new session with optional file uploads.
    
    Args:
        question: The user's core question
        files: Optional list of context files
        db: Database session
        current_user: Current authenticated user
    
    Returns:
        Session ID and context file metadata
    """
    try:
        # Generate session ID
        session_id = SessionManager.generate_session_id()
        
        # Ensure filesystem directories exist
        session_manager.ensure_session_directories(session_id)
        
        # Create metadata in database
        created_at = datetime.now(timezone.utc)
        await SessionService.create_session_metadata(
            db,
            session_id=session_id,
            user_id=current_user.id,
            question=question
        )
        
        # AI Generated Code by Deloitte + Cursor (BEGIN)
        # Initialize state in DB (single source of truth)
        await SessionStateService.init_state(
            db,
            session_id=session_id,
            user_id=current_user.id,
            question=question,
            created_at=created_at
        )
        # AI Generated Code by Deloitte + Cursor (END)

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
        
        # Persist state
        await write_state_primary(
            session_id,
            {
                "session_id": session_id,
                "user_id": current_user.id,
                "question": question,
                "context_files": file_paths,
                "ingested_data": ingested_data,
                "current_step": "build",
                "status": "idle",
                "created_at": created_at.isoformat()
            },
            db=db,
            user_id=current_user.id
        )
        
        # Update database metadata (for listing/filtering only)
        await SessionService.update_session_metadata(
            db,
            session_id,
            {"current_step": "build"}
        )
        
        return {
            "session_id": session_id,
            "question": question,
            "context_files": context_files_meta
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/sessions/{session_id}/build_council")
async def build_council(
    session_id: str,
    force: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Build a council configuration using the Architect agent.
    
    Args:
        session_id: The session identifier
        force: If True, rebuild even if config exists
        db: Database session
        current_user: Current authenticated user
    
    Returns:
        Council configuration
    """
    try:
        # Authorize access
        await authorize_session_access(session_id, current_user.id, db)
        
        state = await read_state_primary(session_id, db, current_user.id)
        
        if not state:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
        
        # Validate question exists
        if not state.get("question"):
            raise HTTPException(status_code=400, detail="Session question is missing")
        
        # Check if council already exists and force is not set
        if state.get("council_config") and not force:
            return state["council_config"]
        
        # Clear any stale execution/review data on rebuild
        if force:
            await write_state_primary(
                session_id,
                {
                    "execution_results": None,
                    "execution_status": {},
                    "execution_error": None,
                    "peer_reviews": None,
                    "aggregated_scores": None,
                    "review_status": {},
                    "review_error": None,
                    "chairman_verdict": None,
                    "status": "build_in_progress",
                    "current_step": "build"
                },
                db=db,
                user_id=current_user.id
            )
        
        question = state["question"]
        ingested_data = state.get("ingested_data", [])
        
        # Create logger (no DB access)
        logs_dir = Path("sessions") / session_id / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        logger = SessionLogger(output_dir=str(logs_dir))
        
        council_config = await AgentCouncilService.build_council(
            question,
            ingested_data,
            logger=logger
        )
        
        # Update state (DB primary, file fallback)
        tokens = logger.get_cost_breakdown()
        await write_state_primary(
            session_id,
            {
                "council_config": council_config,
                "current_step": "edit",
                "status": "build_complete",
                "tokens": tokens
            },
            db=db,
            user_id=current_user.id
        )
        
        # Update database metadata (for listing/filtering)
        await SessionService.update_session_metadata(
            db,
            session_id,
            {
                "current_step": "edit",
                "status": "build_complete",
                "last_cost_usd": tokens.get("total_cost_usd"),
                "last_total_tokens": tokens.get("total_tokens")
            }
        )
        
        return council_config
    
    except HTTPException:
        raise
    except DatabaseBusyError as e:
        raise HTTPException(
            status_code=503,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/sessions/{session_id}/council")
async def update_council(
    session_id: str,
    council_config: CouncilConfig,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update the council configuration.
    
    Args:
        session_id: The session identifier
        council_config: Updated council configuration
        db: Database session
        current_user: Current authenticated user
    
    Returns:
        Success message
    """
    try:
        # Authorize access
        await authorize_session_access(session_id, current_user.id, db)
        
        await write_state_primary(
            session_id,
            {
                "council_config": council_config.model_dump(),
                "execution_results": None,
                "execution_status": {},
                "execution_error": None,
                "peer_reviews": None,
                "aggregated_scores": None,
                "review_status": {},
                "review_error": None,
                "chairman_verdict": None,
                "current_step": "execute",
                "status": "ready_to_execute"
            },
            db=db,
            user_id=current_user.id
        )
        
        # Update database metadata (for listing/filtering)
        await SessionService.update_session_metadata(
            db,
            session_id,
            {
                "current_step": "execute",
                "status": "ready_to_execute"
            }
        )
        
        return {"status": "success", "message": "Council configuration updated"}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def execute_council_task(session_id: str):
    """
    Background task to execute the council.
    Uses DB state with batched progress updates.
    """
    print(f"[EXECUTE_TASK] Starting execution for {session_id}")
    try:
        async with AsyncSessionLocal() as db:
            state = await read_state_primary(session_id, db)
            if not state:
                print(f"[EXECUTE_TASK] Error: Session {session_id} not found")
                return
            
            print(f"[EXECUTE_TASK] State loaded for {session_id}, starting execution...")
            
            council_config = state["council_config"]
            question = state["question"]
            ingested_data = state.get("ingested_data", [])
            
            # Create logger
            logs_dir = Path("sessions") / session_id / "logs"
            logs_dir.mkdir(parents=True, exist_ok=True)
            logger = SessionLogger(output_dir=str(logs_dir))
            print(f"[EXECUTE_TASK] Logger created for {session_id}")
            
            # AI Generated Code by Deloitte + Cursor (BEGIN)
            # Progress callback -> batched DB updates (DB-only state)
            def progress_cb(agent_name: str, status: str):
                asyncio.create_task(
                    SessionStateService.update_state_batched(
                        session_id,
                        {"execution_status": {agent_name: status}},
                        user_id=None
                    )
                )
            # AI Generated Code by Deloitte + Cursor (END)
            
            print(f"[EXECUTE_TASK] About to execute council for {session_id}")
            
            execution_results = await AgentCouncilService.execute_council(
                council_config,
                question,
                ingested_data,
                progress_callback=progress_cb,
                logger=logger
            )
            
            print(f"[EXECUTE_TASK] Execution completed for {session_id}, updating state...")
            
            # Final state update
            tokens = logger.get_cost_breakdown()
            await write_state_primary(
                session_id,
                {
                    "execution_results": execution_results,
                    "current_step": "review",
                    "status": "execution_complete",
                    "tokens": tokens
                },
                db=db
            )
            await SessionService.update_session_metadata(db, session_id, {
                "current_step": "review",
                "status": "execution_complete",
                "last_cost_usd": tokens.get("total_cost_usd"),
                "last_total_tokens": tokens.get("total_tokens")
            })
            await db.commit()
            print(f"[EXECUTE_TASK] State updated for {session_id}")

    except Exception as e:
        print(f"Error in execute_council_task: {e}")
        import traceback
        traceback.print_exc()
        
        try:
            async with AsyncSessionLocal() as db:
                await SessionStateService.update_state(
                    db,
                    session_id,
                    {
                        "execution_error": str(e),
                        "status": "execution_error"
                    }
                )
                await db.commit()
        except Exception as e2:
            print(f"Error updating error state: {e2}")


@app.post("/api/sessions/{session_id}/execute")
async def execute_council(
    session_id: str,
    background_tasks: BackgroundTasks,
    force: bool = False,
    current_user: User = Depends(get_current_user)
):
    """
    Execute the council in parallel (background task).
    
    NOTE: Using manual DB session management to avoid auto-commit issues.
    
    Args:
        session_id: The session identifier
        force: If True, re-execute even if results exist
        current_user: Current authenticated user
    
    Returns:
        Acceptance message
    """
    print(f"[EXECUTE_ENDPOINT] Starting execute for {session_id}")
    
    # Create dedicated DB session for this endpoint
    async with AsyncSessionLocal() as db:
        try:
            # Authorize access
            await authorize_session_access(session_id, current_user.id, db)
            
            state = await read_state_primary(session_id, db, current_user.id)
            
            if not state:
                raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
            
            # Validate preconditions
            if not state.get("council_config"):
                raise HTTPException(
                    status_code=400,
                    detail="Council configuration is required before execution. Please complete the Build step first."
                )
            
            # Check if execution already complete and force is not set
            if state.get("execution_results") and not force:
                return {"status": "already_executed", "message": "Execution already completed. Use force=true to re-execute."}
            
            # Clear previous results if forcing re-execution
            if force and state.get("execution_results"):
                await write_state_primary(
                    session_id,
                    {
                        "execution_results": None,
                        "execution_status": {},
                        "execution_error": None,
                        "peer_reviews": None,
                        "aggregated_scores": None,
                        "review_status": {},
                        "review_error": None,
                        "chairman_verdict": None
                    },
                    db=db,
                    user_id=current_user.id
                )
            
            # Set status to executing in file
            print(f"[EXECUTE_ENDPOINT] Setting status to executing for {session_id}")
            await write_state_primary(
                session_id,
                {
                    "status": "executing",
                    "current_step": "execute"
                },
                db=db,
                user_id=current_user.id
            )
            
            # Update DB metadata
            await SessionService.update_session_metadata(db, session_id, {
                "status": "executing",
                "current_step": "execute"
            })
            await db.commit()
            print(f"[EXECUTE_ENDPOINT] Status written to file and DB for {session_id}")
            
        except HTTPException:
            await db.rollback()
            raise
        except DatabaseBusyError as e:
            await db.rollback()
            raise HTTPException(status_code=503, detail=str(e))
        except Exception as e:
            await db.rollback()
            raise HTTPException(status_code=500, detail=str(e))
    
    # Start background task AFTER closing the DB session
    background_tasks.add_task(execute_council_task, session_id)
    print(f"[EXECUTE_ENDPOINT] Background task started for {session_id}")
    
    return {"status": "accepted", "message": "Execution started"}


@app.get("/api/sessions/{session_id}/status")
async def get_status(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get the current execution/review status.
    Reads from file-based state.json (primary source) with DB fallback.
    
    Args:
        session_id: The session identifier
        db: Database session
        current_user: Current authenticated user
    
    Returns:
        Status information
    """
    try:
        # Authorize access
        await authorize_session_access(session_id, current_user.id, db)
        
        state = await read_state_primary(session_id, db, current_user.id)
        
        if not state:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
        
        # Get status from state (file has most up-to-date info)
        status = state.get("status", "idle")
        
        return {
            "status": status,
            "current_step": state.get("current_step", "unknown"),
            "execution_status": state.get("execution_status", {}),
            "review_status": state.get("review_status", {}),
            "execution_error": state.get("execution_error"),
            "review_error": state.get("review_error"),
            "progress": {
                "execution": state.get("execution_status", {}),
                "review": state.get("review_status", {})
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/sessions/{session_id}/results")
async def get_results(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get execution results.
    Reads from file-based state.json (primary source) with DB fallback.
    
    Args:
        session_id: The session identifier
        db: Database session
        current_user: Current authenticated user
    
    Returns:
        Execution results
    """
    try:
        # Authorize access
        await authorize_session_access(session_id, current_user.id, db)
        
        state = await read_state_primary(session_id, db, current_user.id)
        
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
    """
    Background task to run peer review.
    Uses DB state with batched progress updates.
    """
    print(f"[REVIEW_TASK] Starting peer review for {session_id}")
    try:
        async with AsyncSessionLocal() as db:
            state = await read_state_primary(session_id, db)
            if not state:
                print(f"[REVIEW_TASK] Error: Session {session_id} not found")
                return
            
            council_config = state["council_config"]
            question = state["question"]
            execution_results = state["execution_results"]["execution_results"]
            
            # Create logger
            logs_dir = Path("sessions") / session_id / "logs"
            logs_dir.mkdir(parents=True, exist_ok=True)
            logger = SessionLogger(output_dir=str(logs_dir))
            
            # AI Generated Code by Deloitte + Cursor (BEGIN)
            # Progress callback -> batched DB updates (DB-only state)
            def progress_cb(agent_name: str, status: str):
                asyncio.create_task(
                    SessionStateService.update_state_batched(
                        session_id,
                        {"review_status": {agent_name: status}},
                        user_id=None
                    )
                )
            # AI Generated Code by Deloitte + Cursor (END)
            
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
            
            # Update state
            tokens = logger.get_cost_breakdown()
            await write_state_primary(
                session_id,
                {
                    "peer_reviews": peer_reviews,
                    "aggregated_scores": aggregated_scores,
                    "current_step": "synthesize",
                    "status": "review_complete",
                    "tokens": tokens
                },
                db=db
            )
            await SessionService.update_session_metadata(db, session_id, {
                "current_step": "synthesize",
                "status": "review_complete",
                "last_cost_usd": tokens.get("total_cost_usd"),
                "last_total_tokens": tokens.get("total_tokens")
            })
            await db.commit()
            print(f"[REVIEW_TASK] Peer review completed for {session_id}")
        
    except Exception as e:
        print(f"Error in peer_review_task: {e}")
        import traceback
        traceback.print_exc()
        
        try:
            async with AsyncSessionLocal() as db:
                await SessionStateService.update_state(
                    db,
                    session_id,
                    {
                        "review_error": str(e),
                        "status": "review_error"
                    }
                )
                await db.commit()
        except Exception as e2:
            print(f"Error updating error state: {e2}")


@app.post("/api/sessions/{session_id}/peer_review")
async def peer_review(
    session_id: str,
    background_tasks: BackgroundTasks,
    force: bool = False,
    current_user: User = Depends(get_current_user)
):
    """
    Run peer review process (background task).
    
    NOTE: Using manual DB session management to avoid auto-commit issues.
    
    Args:
        session_id: The session identifier
        force: If True, re-run even if reviews exist
        current_user: Current authenticated user
    
    Returns:
        Acceptance message
    """
    # Create dedicated DB session for this endpoint
    async with AsyncSessionLocal() as db:
        try:
            # Authorize access
            await authorize_session_access(session_id, current_user.id, db)
            
            state = await read_state_primary(session_id, db, current_user.id)
            
            if not state:
                raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
            
            # Validate preconditions
            if not state.get("execution_results"):
                raise HTTPException(
                    status_code=400,
                    detail="Execution results are required before peer review. Please complete the Execute step first."
                )
            
            # Check if peer review already complete and force is not set
            if state.get("peer_reviews") and not force:
                return {"status": "already_reviewed", "message": "Peer review already completed. Use force=true to re-run."}
            
            # Clear previous reviews if forcing re-run
            if force and state.get("peer_reviews"):
                await write_state_primary(
                    session_id,
                    {
                        "peer_reviews": None,
                        "aggregated_scores": None,
                        "review_status": {},
                        "review_error": None,
                        "chairman_verdict": None
                    },
                    db=db,
                    user_id=current_user.id
                )
            
            # Set status to reviewing in file
            await write_state_primary(
                session_id,
                {
                    "status": "reviewing",
                    "current_step": "review"
                },
                db=db,
                user_id=current_user.id
            )
            
            # Update DB metadata
            await SessionService.update_session_metadata(db, session_id, {
                "status": "reviewing",
                "current_step": "review"
            })
            await db.commit()
            
        except HTTPException:
            await db.rollback()
            raise
        except DatabaseBusyError as e:
            await db.rollback()
            raise HTTPException(status_code=503, detail=str(e))
        except Exception as e:
            await db.rollback()
            raise HTTPException(status_code=500, detail=str(e))
    
    # Start background task AFTER closing the DB session
    background_tasks.add_task(peer_review_task, session_id)
    
    return {"status": "accepted", "message": "Peer review started"}


@app.get("/api/sessions/{session_id}/reviews")
async def get_reviews(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get peer review results and aggregated scores.
    Reads from file-based state.json (primary source) with DB fallback.
    
    Args:
        session_id: The session identifier
        db: Database session
        current_user: Current authenticated user
    
    Returns:
        Peer reviews and aggregated scores
    """
    try:
        # Authorize access
        await authorize_session_access(session_id, current_user.id, db)
        
        state = await read_state_primary(session_id, db, current_user.id)
        
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
async def synthesize(
    session_id: str,
    force: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate the Chairman's final verdict.
    
    Args:
        session_id: The session identifier
        force: If True, regenerate even if verdict exists
        db: Database session
        current_user: Current authenticated user
    
    Returns:
        Final verdict
    """
    try:
        # Authorize access
        await authorize_session_access(session_id, current_user.id, db)
        
        state = await read_state_primary(session_id, db, current_user.id)
        
        if not state:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
        
        # Validate preconditions
        if not state.get("execution_results"):
            raise HTTPException(
                status_code=400,
                detail="Execution results are required. Please complete the Execute step first."
            )
        
        if not state.get("peer_reviews"):
            raise HTTPException(
                status_code=400,
                detail="Peer reviews are required. Please complete the Review step first."
            )
        
        # Check if verdict already exists and force is not set
        if state.get("chairman_verdict") and not force:
            return {"verdict": state["chairman_verdict"]}
        
        question = state["question"]
        execution_results = state["execution_results"]["execution_results"]
        peer_reviews = state["peer_reviews"]
        
        # Create logger
        logs_dir = Path("sessions") / session_id / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        logger = SessionLogger(output_dir=str(logs_dir))
        
        final_verdict = await AgentCouncilService.synthesize_verdict(
            question,
            execution_results,
            peer_reviews,
            logger=logger
        )
        
        # Finalize logger
        logger.finalize()
        
        # Update state
        tokens = logger.get_cost_breakdown()
        await write_state_primary(
            session_id,
            {
                "chairman_verdict": final_verdict,
                "current_step": "complete",
                "status": "verdict_complete",
                "tokens": tokens
            },
            db=db,
            user_id=current_user.id
        )
        
        # Update DB metadata
        await SessionService.update_session_metadata(db, session_id, {
            "current_step": "complete",
            "status": "verdict_complete",
            "last_cost_usd": tokens.get("total_cost_usd"),
            "last_total_tokens": tokens.get("total_tokens")
        })
        
        return {"verdict": final_verdict}
    
    except HTTPException:
        raise
    except DatabaseBusyError as e:
        raise HTTPException(
            status_code=503,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/sessions/{session_id}/summary")
async def get_summary(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get complete session summary.
    Reads from file-based state.json (primary source) with DB fallback.
    
    Args:
        session_id: The session identifier
        db: Database session
        current_user: Current authenticated user
    
    Returns:
        Complete session data
    """
    try:
        # Authorize access
        await authorize_session_access(session_id, current_user.id, db)
        
        state = await read_state_primary(session_id, db, current_user.id)
        
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
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/sessions")
async def list_sessions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List all sessions for the current user.
    
    Args:
        db: Database session
        current_user: Current authenticated user
    
    Returns:
        List of sessions with metadata
    """
    try:
        # Get sessions from database filtered by user
        db_sessions = await SessionService.list_user_sessions(
            db,
            user_id=current_user.id,
            include_deleted=False
        )
        
        # Convert to API response format
        sessions = [
            {
                "session_id": sess.id,
                "question": sess.question,
                "current_step": sess.current_step,
                "status": sess.status,
                "created_at": sess.created_at.isoformat(),
                "updated_at": sess.updated_at.isoformat(),
                "last_cost_usd": sess.last_cost_usd,
                "last_total_tokens": sess.last_total_tokens
            }
            for sess in db_sessions
        ]
        
        return {"sessions": sessions}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/sessions/{session_id}")
async def delete_session(
    session_id: str,
    hard: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a session (soft delete by default).
    
    Args:
        session_id: The session identifier
        hard: If True, permanently delete files and DB state; if False, soft delete
        db: Database session
        current_user: Current authenticated user
    
    Returns:
        Success message
    """
    try:
        # Soft delete in database
        deleted = await SessionService.soft_delete_session(
            db,
            session_id,
            current_user.id
        )
        
        if not deleted:
            raise HTTPException(
                status_code=404,
                detail=f"Session {session_id} not found or you don't have access"
            )
        
        # If hard delete requested, remove filesystem data and clear DB state
        if hard:
            session_manager.delete_session(session_id)
            # Optionally clear state JSON in DB too
            await SessionStateService.update_state(db, session_id, {
                "deleted": True
            }, user_id=current_user.id)
            message = "Session permanently deleted"
        else:
            # Mark as deleted in DB state as well
            await SessionStateService.update_state(db, session_id, {
                "deleted": True
            }, user_id=current_user.id)
            message = "Session soft-deleted (hidden from list, files preserved)"
        
        return {"status": "success", "message": message}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
