#!/usr/bin/env python3
"""
Utility script to promote a user to admin role.

Usage:
    python scripts/promote_user_to_admin.py <external_id>
    
Example:
    python scripts/promote_user_to_admin.py admin@example.com

This script is intended for development and testing. In production,
role assignment should be handled via SSO app-role mapping.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.web.database import AsyncSessionLocal, init_db
from src.web.db_service import UserService


async def promote_user(external_id: str):
    """Promote a user to admin role."""
    # Initialize database (run migrations if needed)
    await init_db()
    
    async with AsyncSessionLocal() as session:
        user = await UserService.update_role(
            session,
            external_id=external_id,
            new_role="admin"
        )
        
        if not user:
            print(f"Error: User '{external_id}' not found.")
            print("Note: Users are created on first API access. Try accessing the API first.")
            return 1
        
        await session.commit()
        print(f"✓ Successfully promoted '{external_id}' to admin role.")
        print(f"  User ID: {user.id}")
        print(f"  Display Name: {user.display_name}")
        print(f"  Role: {user.role}")
        return 0


async def main():
    """Main entry point."""
    if len(sys.argv) != 2:
        print("Usage: python scripts/promote_user_to_admin.py <external_id>")
        print("Example: python scripts/promote_user_to_admin.py admin@example.com")
        return 1
    
    external_id = sys.argv[1]
    return await promote_user(external_id)


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

