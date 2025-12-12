"""Add role column to users table

Revision ID: 8b746e4b0150
Revises: 950bd54c7a60
Create Date: 2025-12-12 15:55:27.652755

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# AI Generated Code by Deloitte + Cursor (BEGIN)

# revision identifiers, used by Alembic.
revision: str = '8b746e4b0150'
down_revision: Union[str, Sequence[str], None] = '950bd54c7a60'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: add role column to users table."""
    # Detect database type
    bind = op.get_bind()
    is_sqlite = bind.dialect.name == 'sqlite'
    is_postgres = bind.dialect.name == 'postgresql'
    
    if is_sqlite:
        # SQLite doesn't support ALTER COLUMN, so we need to recreate the table
        # Step 1: Create new table with role column
        op.create_table(
            'users_new',
            sa.Column('id', sa.String(), nullable=False),
            sa.Column('external_id', sa.String(), nullable=False),
            sa.Column('display_name', sa.String(), nullable=True),
            sa.Column('role', sa.String(), nullable=False, server_default='user'),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_users_external_id'), 'users_new', ['external_id'], unique=True)
        op.create_index(op.f('ix_users_role'), 'users_new', ['role'], unique=False)
        
        # Step 2: Copy data from old table, setting role='user' for existing rows
        op.execute(sa.text(
            "INSERT INTO users_new (id, external_id, display_name, role, created_at, updated_at) "
            "SELECT id, external_id, display_name, 'user', created_at, updated_at FROM users"
        ))
        
        # Step 3: Drop old table and rename new table
        op.drop_table('users')
        op.rename_table('users_new', 'users')
    else:
        # PostgreSQL and other databases support ALTER COLUMN
        # Add role column with default value 'user' (nullable initially for existing rows)
        op.add_column('users', sa.Column('role', sa.String(), nullable=True, server_default='user'))
        
        # Update existing rows to have 'user' role (in case server_default didn't apply)
        op.execute(sa.text("UPDATE users SET role = 'user' WHERE role IS NULL"))
        
        # Make column non-nullable now that all rows have values
        op.alter_column('users', 'role', nullable=False, server_default='user')
        
        # Create index on role for faster role-based queries
        op.create_index(op.f('ix_users_role'), 'users', ['role'], unique=False)


def downgrade() -> None:
    """Downgrade schema: remove role column from users table."""
    # Detect database type
    bind = op.get_bind()
    is_sqlite = bind.dialect.name == 'sqlite'
    
    if is_sqlite:
        # SQLite: recreate table without role column
        op.create_table(
            'users_old',
            sa.Column('id', sa.String(), nullable=False),
            sa.Column('external_id', sa.String(), nullable=False),
            sa.Column('display_name', sa.String(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_users_external_id'), 'users_old', ['external_id'], unique=True)
        
        op.execute(sa.text(
            "INSERT INTO users_old (id, external_id, display_name, created_at, updated_at) "
            "SELECT id, external_id, display_name, created_at, updated_at FROM users"
        ))
        
        op.drop_table('users')
        op.rename_table('users_old', 'users')
    else:
        # PostgreSQL and other databases
        op.drop_index(op.f('ix_users_role'), table_name='users')
        op.drop_column('users', 'role')
# AI Generated Code by Deloitte + Cursor (END)
