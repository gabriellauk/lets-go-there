"""Add travel_idea_group_invitation table

Revision ID: 8af9c0dba3d0
Revises: e1b007ed5bae
Create Date: 2025-12-02 19:37:02.104004

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8af9c0dba3d0'
down_revision: Union[str, Sequence[str], None] = 'e1b007ed5bae'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('travel_idea_group_invitation',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('email', sa.String(length=255), nullable=False),
    sa.Column('invitation_code', sa.String(length=10), nullable=False),
    sa.Column('status', sa.Enum('pending', 'rejected', 'accepted', name='travelideagroupinvitationstatus'), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('created_by_id', sa.Integer(), nullable=False),
    sa.Column('travel_idea_group_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['created_by_id'], ['user_account.id'], name=op.f('fk_travel_idea_group_invitation_created_by_id_user_account')),
    sa.ForeignKeyConstraint(['travel_idea_group_id'], ['travel_idea_group.id'], name=op.f('fk_travel_idea_group_invitation_travel_idea_group_id_travel_idea_group')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_travel_idea_group_invitation')),
    sa.UniqueConstraint('invitation_code', name=op.f('uq_travel_idea_group_invitation_invitation_code'))
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('travel_idea_group_invitation')
    op.execute('DROP TYPE IF EXISTS travelideagroupinvitationstatus')