"""upload status column updated

Revision ID: a8a3122221ed
Revises: bebf7ad43bb5
Create Date: 2025-08-01 14:15:14.843004

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'a8a3122221ed'
down_revision: Union[str, None] = 'bebf7ad43bb5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # Step 1: Add new integer column (nullable for now)
    op.add_column('videos', sa.Column('upload_status_int', sa.Integer(), nullable=True))

    # Step 2: Map Enum values to integers manually
    status_map = {
        'pending': 0,
        'processing': 1,
        'ready': 2,
        'failed': 3
    }

    # Step 2 continued: Populate new int column
    for status_str, status_int in status_map.items():
        op.execute(
            f"UPDATE videos SET upload_status_int = {status_int} WHERE upload_status = '{status_str}'"
        )

    # Step 3: Drop the original Enum column
    op.drop_column('videos', 'upload_status')

    # Step 4: Rename new column to original name
    op.alter_column('videos', 'upload_status_int', new_column_name='upload_status')

    # Step 5: Make new column NOT NULL (if needed)
    op.alter_column('videos', 'upload_status', nullable=False)


def downgrade():
    # Reverse of the upgrade (if needed)

    # Step 1: Add back the original Enum column (nullable)
    upload_status_enum = sa.Enum('pending', 'processing', 'ready', 'failed', name='uploadstatusenum')
    op.add_column('videos', sa.Column('upload_status_enum_tmp', upload_status_enum, nullable=True))

    # Step 2: Map integers back to Enum strings
    reverse_map = {
        0: 'pending',
        1: 'processing',
        2: 'ready',
        3: 'failed'
    }

    for int_val, enum_str in reverse_map.items():
        op.execute(
            f"UPDATE videos SET upload_status_enum_tmp = '{enum_str}' WHERE upload_status = {int_val}"
        )

    # Step 3: Drop integer column
    op.drop_column('videos', 'upload_status')

    # Step 4: Rename enum column back to original name
    op.alter_column('videos', 'upload_status_enum_tmp', new_column_name='upload_status')

    # Step 5: Set NOT NULL if needed
    op.alter_column('videos', 'upload_status', nullable=False)
