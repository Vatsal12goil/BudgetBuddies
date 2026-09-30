"""add user profile fields

Revision ID: 5c2e8a1f4d77
Revises: 0b906702b3eb
Create Date: 2026-09-30

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "5c2e8a1f4d77"
down_revision: Union[str, Sequence[str], None] = "0b906702b3eb"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.add_column("users", sa.Column("monthly_income", sa.Float(), nullable=True))
    op.add_column("users", sa.Column("financial_preference", sa.String(), nullable=True))
    op.add_column("users", sa.Column("account_setting", sa.String(), nullable=True))

def downgrade() -> None:
    op.drop_column("users", "account_setting")
    op.drop_column("users", "financial_preference")
    op.drop_column("users", "monthly_income")
