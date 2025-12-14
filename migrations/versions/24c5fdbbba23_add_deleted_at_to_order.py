"""add deleted_at to order

Revision ID: 24c5fdbbba23
Revises: 8f5541e678d9
Create Date: 2025-12-14 04:15:54.794175

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa



# revision identifiers, used by Alembic.
revision: str = '24c5fdbbba23'
down_revision: Union[str, Sequence[str], None] = '8f5541e678d9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.add_column("order", sa.Column("deleted_at", sa.DateTime(), nullable=True))
def downgrade() -> None:
    op.drop_column("order", "deleted_at")