from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "75f4f42cb1c9"
down_revision: Union[str, Sequence[str], None] = "e2e7e483d167"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        "cart",
        sa.Column("cart_id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user.user_id"], ondelete="CASCADE"),
        sa.UniqueConstraint("user_id"),
    )

    op.create_table(
        "cart_item",
        sa.Column("cart_item_id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("cart_id", sa.BigInteger(), nullable=False),
        sa.Column("book_id", sa.BigInteger(), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["cart_id"], ["cart.cart_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["book_id"], ["book.book_id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("cart_id", "book_id", name="uq_cart_item_cart_book"),
    )

def downgrade() -> None:
    op.drop_table("cart_item")
    op.drop_table("cart")
