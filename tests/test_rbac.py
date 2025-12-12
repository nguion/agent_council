"""
Tests for RBAC (Role-Based Access Control) functionality.

Tests:
- Role enforcement via require_role() dependency
- Admin endpoint access control
- Non-admin user rejection
- Default role assignment for new users
"""
import asyncio
import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from src.web.database import User
from src.web.db_service import UserService


class TestRBACRoleEnforcement:
    """Test require_role() dependency enforcement."""
    
    def test_admin_endpoint_allows_admin_user(self, client: TestClient, test_db):
        """Admin endpoint should allow users with 'admin' role."""
        # Create admin user using async database session
        async def create_admin_user():
            async with test_db() as session:
                admin_user = await UserService.get_or_create_user(
                    session,
                    external_id="admin@example.com",
                    display_name="Admin User"
                )
                # Update role to admin
                admin_user.role = "admin"
                await session.commit()
                return admin_user.id
        
        admin_user_id = asyncio.run(create_admin_user())
        assert admin_user_id is not None
        
        # Make request as admin user
        response = client.get(
            "/api/admin/metrics/summary",
            headers={"X-User-Id": "admin@example.com"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "total_sessions" in data
        assert "active_users" in data
        assert data["note"] == "Placeholder metrics - real implementation in Sprint 2"
    
    def test_admin_endpoint_rejects_regular_user(self, client: TestClient):
        """Admin endpoint should reject users with 'user' role."""
        # Regular user is created automatically by get_current_user with default 'user' role
        response = client.get(
            "/api/admin/metrics/summary",
            headers={"X-User-Id": "regular@example.com"}
        )
        
        assert response.status_code == 403
        data = response.json()
        assert "Access denied" in data["detail"]
        assert "admin" in data["detail"]
        assert "user" in data["detail"]
    
    def test_admin_endpoint_rejects_auditor_role(self, client: TestClient, test_db):
        """Admin endpoint should reject users with 'auditor' role."""
        # Create auditor user
        async def create_auditor_user():
            async with test_db() as session:
                auditor_user = await UserService.get_or_create_user(
                    session,
                    external_id="auditor@example.com",
                    display_name="Auditor User"
                )
                # Update role to auditor
                auditor_user.role = "auditor"
                await session.commit()
                return auditor_user.id
        
        auditor_user_id = asyncio.run(create_auditor_user())
        assert auditor_user_id is not None
        
        # Make request as auditor user
        response = client.get(
            "/api/admin/metrics/summary",
            headers={"X-User-Id": "auditor@example.com"}
        )
        
        assert response.status_code == 403
        data = response.json()
        assert "Access denied" in data["detail"]
        assert "admin" in data["detail"]
        assert "auditor" in data["detail"]


class TestDefaultRoleAssignment:
    """Test that new users get default 'user' role."""
    
    def test_new_user_gets_default_role(self, client: TestClient, test_db):
        """New users should be created with role='user' by default."""
        # Create a new user via API call
        response = client.post(
            "/api/sessions",
            data={"question": "Test question?"},
            headers={"X-User-Id": "newuser@example.com"}
        )
        
        assert response.status_code == 200
        
        # Verify user was created with 'user' role
        async def check_user_role():
            async with test_db() as session:
                result = await session.execute(
                    select(User).where(User.external_id == "newuser@example.com")
                )
                user = result.scalar_one_or_none()
                assert user is not None
                assert user.role == "user"
                return user.role
        
        role = asyncio.run(check_user_role())
        assert role == "user"
    
    def test_existing_user_role_preserved(self, client: TestClient, test_db):
        """Existing users should keep their role when accessed again."""
        # Create admin user
        async def create_admin_user():
            async with test_db() as session:
                admin_user = await UserService.get_or_create_user(
                    session,
                    external_id="existing-admin@example.com",
                    display_name="Existing Admin"
                )
                admin_user.role = "admin"
                await session.commit()
                return admin_user.id
        
        admin_user_id = asyncio.run(create_admin_user())
        assert admin_user_id is not None
        
        # Access API as this user
        response = client.post(
            "/api/sessions",
            data={"question": "Test question?"},
            headers={"X-User-Id": "existing-admin@example.com"}
        )
        
        assert response.status_code == 200
        
        # Verify role is still 'admin'
        async def check_user_role():
            async with test_db() as session:
                result = await session.execute(
                    select(User).where(User.external_id == "existing-admin@example.com")
                )
                user = result.scalar_one_or_none()
                assert user is not None
                assert user.role == "admin"
                return user.role
        
        role = asyncio.run(check_user_role())
        assert role == "admin"


class TestRoleMigration:
    """Test that role column migration works correctly."""
    
    def test_users_table_has_role_column(self, client: TestClient, test_db):
        """Verify that users table has role column after migration."""
        # This test verifies the migration was applied
        async def check_column():
            async with test_db() as session:
                # Try to query role column - if it doesn't exist, this will fail
                result = await session.execute(
                    select(User.role).limit(1)
                )
                # If we get here, the column exists
                return True
        
        # Migration should have been applied by init_db() in conftest
        column_exists = asyncio.run(check_column())
        assert column_exists

