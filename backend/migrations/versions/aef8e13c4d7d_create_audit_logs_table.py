"""create audit logs table

Revision ID: aef8e13c4d7d
Revises: 3f2f3c6afc37
Create Date: 2026-08-06 14:43:29.579125

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "aef8e13c4d7d"
down_revision: Union[str, Sequence[str], None] = "3f2f3c6afc37"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Use the EXISTING PostgreSQL enum.
user_role_enum = postgresql.ENUM(
    "ADMIN",
    "DOCTOR",
    "RECEPTIONIST",
    "PHARMACIST",
    "LAB_TECHNICIAN",
    "RESEARCHER",
    name="userrole",
    create_type=False,
)


def upgrade() -> None:
    """Upgrade schema."""

    op.create_table(
        "audit_logs",

        sa.Column(
            "id",
            sa.Uuid(),
            nullable=False,
        ),

        sa.Column(
            "user_id",
            sa.Uuid(),
            nullable=False,
        ),

        sa.Column(
            "user_email",
            sa.String(length=255),
            nullable=False,
        ),

        sa.Column(
            "role",
            user_role_enum,
            nullable=False,
        ),

        sa.Column(
            "module",
            sa.String(length=100),
            nullable=False,
        ),

        sa.Column(
            "action",
            sa.String(length=50),
            nullable=False,
        ),

        sa.Column(
            "record_id",
            sa.String(length=100),
            nullable=True,
        ),

        sa.Column(
            "description",
            sa.Text(),
            nullable=False,
        ),

        sa.Column(
            "endpoint",
            sa.String(length=255),
            nullable=True,
        ),

        sa.Column(
            "http_method",
            sa.String(length=10),
            nullable=True,
        ),

        sa.Column(
            "ip_address",
            sa.String(length=50),
            nullable=True,
        ),

        sa.Column(
            "user_agent",
            sa.Text(),
            nullable=True,
        ),

        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),

        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),

        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),

        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_audit_logs_user_id",
        "audit_logs",
        ["user_id"],
    )

    op.create_index(
        "ix_audit_logs_module",
        "audit_logs",
        ["module"],
    )

    op.create_index(
        "ix_audit_logs_action",
        "audit_logs",
        ["action"],
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_index(
        "ix_audit_logs_action",
        table_name="audit_logs",
    )

    op.drop_index(
        "ix_audit_logs_module",
        table_name="audit_logs",
    )

    op.drop_index(
        "ix_audit_logs_user_id",
        table_name="audit_logs",
    )

    op.drop_table("audit_logs")