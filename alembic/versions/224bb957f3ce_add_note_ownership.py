"""add note ownership

Revision ID: 224bb957f3ce
Revises: 9a6163a6d476
Create Date: 2026-09-23 17:01:05.184638

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '224bb957f3ce'
down_revision: Union[str, Sequence[str], None] = '9a6163a6d476'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    # 1. Add user_id temporarily allowing NULL values.
    # Existing notes do not have an owner yet.
    op.add_column(
        "notes",
        sa.Column("user_id", sa.Integer(), nullable=True)
    )

    # 2. Legacy notes have no reliable owner, so remove them.
    op.execute(
        "DELETE FROM notes WHERE user_id IS NULL"
    )

    # 3. From now on every note must have an owner.
    op.alter_column(
        "notes",
        "user_id",
        existing_type=sa.Integer(),
        nullable=False
    )

    # 4. Explicitly named foreign key.
    op.create_foreign_key(
        "fk_notes_user_id_users",
        "notes",
        "users",
        ["user_id"],
        ["id"]
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_constraint(
        "fk_notes_user_id_users",
        "notes",
        type_="foreignkey"
    )

    op.drop_column(
        "notes",
        "user_id"
    )
