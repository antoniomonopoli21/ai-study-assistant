"""enable pgvector extension

Revision ID: 744072c26646
Revises: 290d8cb907fc
Create Date: 2026-09-28 19:12:39.542417

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '744072c26646'
down_revision: Union[str, Sequence[str], None] = '290d8cb907fc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "CREATE EXTENSION IF NOT EXISTS vector"
    )
    


def downgrade() -> None:
    op.execute(
        "DROP EXTENSION IF EXISTS vector"
    )