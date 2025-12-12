"""
Migration script to backfill state.json files into the database.

This script migrates existing file-based session state into the database
for the new DB-backed state management system.

Usage:
    python migrate_state_json_to_db.py
"""

import asyncio
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# AI Generated Code by Deloitte + Cursor (BEGIN)
# Add project root to path for imports (so `src.*` namespace imports work)
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))
# AI Generated Code by Deloitte + Cursor (END)

from src.web.database import AsyncSessionLocal, SessionState, User, init_db  # noqa: E402
from src.web.database import Session as DBSession  # noqa: E402
from src.web.db_service import SessionService, UserService  # noqa: E402


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
                with open(state_file, encoding='utf-8') as f:
                    state = json.load(f)

                # AI Generated Code by Deloitte + Cursor (BEGIN)
                # Skip if already migrated (SessionState exists)
                existing_state = await db.get(SessionState, session_id)
                if existing_state:
                    print(f"⊘ {session_id}: Already migrated (SessionState), skipping")
                    skipped_count += 1
                    continue

                # Resolve/assign user ownership
                state_user_value = state.get("user_id")
                resolved_user_id = None

                if isinstance(state_user_value, str) and state_user_value.strip():
                    # If it matches an existing internal user id, keep it
                    existing_user = await db.get(User, state_user_value)
                    if existing_user:
                        resolved_user_id = existing_user.id
                    # If it looks like an email/UPN, create/find user by external_id
                    elif "@" in state_user_value:
                        user = await UserService.get_or_create_user(db, external_id=state_user_value)
                        resolved_user_id = user.id

                if not resolved_user_id:
                    admin_external_id = os.getenv("MIGRATION_ADMIN_EXTERNAL_ID", "admin@deloitte.com")
                    admin_user = await UserService.get_or_create_user(db, external_id=admin_external_id, display_name="Admin")
                    resolved_user_id = admin_user.id
                    if not state_user_value:
                        print(f"  ⚠ No user_id in state, assigning to {admin_external_id}")
                    else:
                        print(f"  ⚠ Could not resolve user_id={state_user_value!r}, assigning to {admin_external_id}")

                # Ensure session metadata exists
                db_session = await db.get(DBSession, session_id)
                if not db_session:
                    question = state.get("question", "Migrated session")
                    await SessionService.create_session_metadata(
                        db,
                        session_id=session_id,
                        user_id=resolved_user_id,
                        question=question,
                    )

                # Normalize state for DB storage
                state["session_id"] = session_id
                state["user_id"] = resolved_user_id
                if not state.get("created_at"):
                    state["created_at"] = datetime.now(timezone.utc).isoformat()
                state["updated_at"] = datetime.now(timezone.utc).isoformat()

                # Persist DB state
                db.add(SessionState(session_id=session_id, state=state, updated_at=datetime.now(timezone.utc)))

                # Sync metadata from state
                if state.get("chairman_verdict"):
                    derived_status = "verdict_complete"
                elif state.get("peer_reviews"):
                    derived_status = "review_complete"
                elif state.get("execution_results"):
                    derived_status = "execution_complete"
                else:
                    derived_status = state.get("status", "idle")

                tokens = state.get("tokens", {}) if isinstance(state.get("tokens"), dict) else {}
                meta_updates = {
                    "current_step": state.get("current_step", "complete"),
                    "status": derived_status,
                }
                if "total_cost_usd" in tokens:
                    meta_updates["last_cost_usd"] = tokens.get("total_cost_usd")
                if "total_tokens" in tokens:
                    meta_updates["last_total_tokens"] = tokens.get("total_tokens")

                await SessionService.update_session_metadata(db, session_id, meta_updates)

                print(f"✓ {session_id}: Migrated (SessionState)")
                migrated_count += 1
                # AI Generated Code by Deloitte + Cursor (END)
                
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

