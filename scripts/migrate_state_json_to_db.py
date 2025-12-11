"""
Migration script to backfill state.json files into the database.

This script migrates existing file-based session state into the database
for the new DB-backed state management system.

Usage:
    python migrate_state_json_to_db.py
"""

import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.web.database import init_db, AsyncSessionLocal
from src.web.db_service import UserService, SessionService
from src.web.state_service import SessionStateService


async def migrate_sessions():
    """Migrate all sessions from state.json to database."""
    
    print("=" * 60)
    print("  State.json to Database Migration")
    print("=" * 60)
    print()
    
    # Initialize database
    print("Initializing database...")
    await init_db()
    print("✓ Database initialized")
    print()
    
    sessions_dir = Path("sessions")
    if not sessions_dir.exists():
        print("No sessions directory found. Nothing to migrate.")
        return
    
    # Scan for sessions
    session_dirs = [d for d in sessions_dir.iterdir() if d.is_dir()]
    
    if not session_dirs:
        print("No session directories found. Nothing to migrate.")
        return
    
    print(f"Found {len(session_dirs)} session directories to scan")
    print()
    
    migrated_count = 0
    skipped_count = 0
    error_count = 0
    
    async with AsyncSessionLocal() as db:
        for session_dir in session_dirs:
            session_id = session_dir.name
            state_file = session_dir / "state.json"
            
            # Skip if no state.json exists
            if not state_file.exists():
                print(f"⊘ {session_id}: No state.json file, skipping")
                skipped_count += 1
                continue
            
            try:
                # Load state from file
                with open(state_file, 'r', encoding='utf-8') as f:
                    state = json.load(f)
                
                # Check if session exists in DB
                from sqlalchemy import select
                from src.web.database import Session as DBSession
                result = await db.execute(
                    select(DBSession).where(DBSession.id == session_id)
                )
                db_session = result.scalar_one_or_none()
                
                if db_session:
                    # Check if already migrated (has state JSON)
                    if db_session.state is not None:
                        print(f"⊘ {session_id}: Already migrated, skipping")
                        skipped_count += 1
                        continue
                    
                    # Update existing session with state
                    db_session.state = state
                    
                    # Sync metadata from state
                    if "question" in state and not db_session.question:
                        db_session.question = state["question"]
                    if "current_step" in state:
                        db_session.current_step = state.get("current_step", "complete")
                    
                    # Derive status from state
                    if state.get("chairman_verdict"):
                        db_session.status = "verdict_complete"
                    elif state.get("peer_reviews"):
                        db_session.status = "review_complete"
                    elif state.get("execution_results"):
                        db_session.status = "execution_complete"
                    else:
                        db_session.status = state.get("status", "idle")
                    
                    # Update cost/token info
                    tokens = state.get("tokens", {})
                    if "total_cost_usd" in tokens:
                        db_session.last_cost_usd = tokens["total_cost_usd"]
                    if "total_tokens" in tokens:
                        db_session.last_total_tokens = tokens["total_tokens"]
                    
                    db_session.updated_at = datetime.utcnow()
                    
                    print(f"✓ {session_id}: Migrated (existing DB entry)")
                    migrated_count += 1
                
                else:
                    # Session doesn't exist in DB - need to create it
                    user_id = state.get("user_id")
                    
                    if not user_id:
                        # Create a default admin user for orphaned sessions
                        admin_user = await UserService.get_or_create_user(
                            db,
                            "admin@deloitte.com",
                            "Admin"
                        )
                        user_id = admin_user.id
                        print(f"  ⚠ No user_id in state, assigning to admin@deloitte.com")
                    else:
                        # Ensure user exists
                        user = await UserService.get_or_create_user(
                            db,
                            user_id,
                            user_id.split('@')[0] if '@' in user_id else user_id
                        )
                        user_id = user.id
                    
                    # Create session metadata
                    question = state.get("question", "Migrated session")
                    created_at_str = state.get("created_at")
                    created_at = datetime.fromisoformat(created_at_str) if created_at_str else datetime.utcnow()
                    
                    # Derive status
                    if state.get("chairman_verdict"):
                        status = "verdict_complete"
                    elif state.get("peer_reviews"):
                        status = "review_complete"
                    elif state.get("execution_results"):
                        status = "execution_complete"
                    else:
                        status = state.get("status", "idle")
                    
                    from src.web.database import Session as DBSession
                    new_session = DBSession(
                        id=session_id,
                        user_id=user_id,
                        question=question,
                        current_step=state.get("current_step", "complete"),
                        status=status,
                        created_at=created_at,
                        updated_at=datetime.utcnow(),
                        is_deleted=False,
                        state=state
                    )
                    
                    # Set cost/token info
                    tokens = state.get("tokens", {})
                    if "total_cost_usd" in tokens:
                        new_session.last_cost_usd = tokens["total_cost_usd"]
                    if "total_tokens" in tokens:
                        new_session.last_total_tokens = tokens["total_tokens"]
                    
                    db.add(new_session)
                    
                    print(f"✓ {session_id}: Migrated (created new DB entry)")
                    migrated_count += 1
                
            except Exception as e:
                print(f"✗ {session_id}: Error - {e}")
                error_count += 1
                continue
        
        # Commit all changes
        try:
            await db.commit()
            print()
            print("✓ All changes committed to database")
        except Exception as e:
            print()
            print(f"✗ Error committing changes: {e}")
            await db.rollback()
            return
    
    print()
    print("=" * 60)
    print("  Migration Summary")
    print("=" * 60)
    print(f"  Total sessions scanned: {len(session_dirs)}")
    print(f"  Migrated: {migrated_count}")
    print(f"  Skipped: {skipped_count}")
    print(f"  Errors: {error_count}")
    print("=" * 60)
    print()
    
    if migrated_count > 0:
        print("✓ Migration complete!")
        print()
        print("Note: Original state.json files are preserved.")
        print("You can safely delete them after verifying the migration.")
    else:
        print("No sessions were migrated.")


if __name__ == "__main__":
    asyncio.run(migrate_sessions())
