"""add role and status to users

Adds the user role (USER | ADMIN) and approval status
(PENDING | APPROVED | REJECTED) columns used by the admin approval workflow.

Existing rows are back-filled to an APPROVED regular USER so no current user is
locked out and no data is lost. New sign-ups default to role=USER /
status=PENDING at the application layer.

Revision ID: 0001_add_user_role_status
Revises:
Create Date: 2026-07-15
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0001_add_user_role_status"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add columns with a server default so pre-existing rows are back-filled to
    # an APPROVED regular USER (no data loss / no lock-outs).
    op.add_column(
        "users",
        sa.Column(
            "role",
            sa.String(length=10),
            nullable=False,
            server_default="USER",
        ),
    )
    op.add_column(
        "users",
        sa.Column(
            "status",
            sa.String(length=10),
            nullable=False,
            server_default="APPROVED",
        ),
    )


def downgrade() -> None:
    op.drop_column("users", "status")
    op.drop_column("users", "role")
