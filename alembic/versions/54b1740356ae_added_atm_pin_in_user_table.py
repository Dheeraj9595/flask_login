"""added atm_pin in User table

Revision ID: 54b1740356ae
Revises: 7b29ae2ccea2
Create Date: 2024-11-26 12:54:51.190312

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '54b1740356ae'
down_revision: Union[str, None] = '7b29ae2ccea2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('user', sa.Column('atm_pin', sa.Integer(), nullable=True))
    op.create_index(op.f('ix_user_atm_pin'), 'user', ['atm_pin'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_user_atm_pin'), table_name='user')
    op.drop_column('user', 'atm_pin')
    # ### end Alembic commands ###
