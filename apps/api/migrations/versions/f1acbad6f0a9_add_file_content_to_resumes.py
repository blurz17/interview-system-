"""add_file_content_to_resumes

Revision ID: f1acbad6f0a9
Revises: 82eb110f72f7
Create Date: 2026-10-26 16:33:14.856532

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f1acbad6f0a9'
down_revision: Union[str, None] = '82eb110f72f7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("resumes", sa.Column("file_content", sa.LargeBinary(), nullable=True))


def downgrade() -> None:
    op.drop_column("resumes", "file_content")
