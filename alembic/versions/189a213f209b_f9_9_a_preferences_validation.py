"""f9_9_a_preferences_validation

F9.9-A: Validate user_preferences table exists and has correct indexes.
This is a minimal migration that verifies the schema without destructive changes.

Table user_preferences should already exist (wide-column format).
This migration ensures indexes are present for performance.

Revision ID: 189a213f209b
Revises: da44f6d378a1
Create Date: 2026-01-04 22:05:14.628275

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine import reflection


# revision identifiers, used by Alembic.
revision: str = '189a213f209b'
down_revision: Union[str, Sequence[str], None] = 'da44f6d378a1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Validate user_preferences table and ensure indexes exist.
    
    Idempotent: creates indexes only if they don't exist.
    Fail-closed: raises error if table is missing.
    """
    conn = op.get_bind()
    inspector = reflection.Inspector.from_engine(conn)
    
    # Verify table exists
    tables = inspector.get_table_names()
    if "user_preferences" not in tables:
        raise RuntimeError(
            "F9.9-A migration failed: user_preferences table does not exist. "
            "Expected table created in prior migration or manual setup."
        )
    
    # Get existing indexes
    indexes = inspector.get_indexes("user_preferences")
    index_names = {idx["name"] for idx in indexes}
    
    # Create index on user_id if not exists (should already exist as UNIQUE)
    if "ix_user_preferences_user_id" not in index_names:
        op.create_index(
            "ix_user_preferences_user_id",
            "user_preferences",
            ["user_id"],
            unique=True
        )
    
    # Validation successful - no structural changes needed
    print("✅ F9.9-A migration: user_preferences validated, indexes verified")


def downgrade() -> None:
    """
    Downgrade: no-op (table preserved).
    
    This migration does not create the table, so rollback is safe.
    Indexes remain (harmless, improve performance).
    """
    # No-op: preserve existing schema
    print("✅ F9.9-A rollback: no schema changes to revert (validation only)")
    pass

