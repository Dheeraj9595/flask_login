"""removed user id

Revision ID: 5a476562ddbb
Revises: 83a822c37adb
Create Date: 2024-11-25 15:56:57.971098

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5a476562ddbb'
down_revision: Union[str, None] = '83a822c37adb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('notifications', 'user_id')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('notifications', sa.Column('user_id', sa.INTEGER(), nullable=True))
    # ### end Alembic commands ###
