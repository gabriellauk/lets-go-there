"""Remove password_hash on user_account

Revision ID: 5e3b78147a7d
Revises: 8af9c0dba3d0
Create Date: 2025-12-08 23:16:45.814945

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5e3b78147a7d'
down_revision: Union[str, Sequence[str], None] = '8af9c0dba3d0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_column('user_account', 'password_hash')


def downgrade() -> None:
    """Downgrade schema."""
    pass
