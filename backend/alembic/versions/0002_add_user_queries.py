"""add user_queries table (user query history)

Creates the ``user_queries`` table that records each drug-assistant lookup a
user makes, linked to the users (registration) table by a cascading foreign key.

Revision ID: 0002_add_user_queries
Revises: 0001_add_user_role_status
Create Date: 2026-07-16
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0002_add_user_queries"
down_revision = "0001_add_user_role_status"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "user_queries",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("query_text", sa.String(length=120), nullable=False),
        sa.Column("recognized", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("result", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_user_queries_user_id", "user_queries", ["user_id"])
    op.create_index("ix_user_queries_created_at", "user_queries", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_user_queries_created_at", table_name="user_queries")
    op.drop_index("ix_user_queries_user_id", table_name="user_queries")
    op.drop_table("user_queries")
