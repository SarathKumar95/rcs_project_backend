"""Change created_by from UUID to Integer

Revision ID: c6dd8bf3fb87
Revises: a8a3122221ed
Create Date: 2025-08-28 11:38:04.691150

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c6dd8bf3fb87'
down_revision: Union[str, None] = 'a8a3122221ed'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade():
    # Drop the old UUID column
    op.drop_column("videos", "created_by")

    # Add the new Integer column
    op.add_column(
        "videos",
        sa.Column("created_by", sa.Integer(), nullable=False)
    )


def downgrade():
    # Drop the Integer column
    op.drop_column("videos", "created_by")

    # Recreate the UUID column in case of rollback
    op.add_column(
        "videos",
        sa.Column("created_by", sa.dialects.postgresql.UUID(), nullable=False)
    )