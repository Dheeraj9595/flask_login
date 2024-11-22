"""email field made non unique

Revision ID: a77e0dfe4b3a
Revises: 0295343f6638
Create Date: 2024-11-19 19:26:12.969133

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a77e0dfe4b3a'
down_revision: Union[str, None] = '0295343f6638'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index('ix_user_email', table_name='user')
    op.create_index(op.f('ix_user_email'), 'user', ['email'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_user_email'), table_name='user')
    op.create_index('ix_user_email', 'user', ['email'], unique=1)
    # ### end Alembic commands ###