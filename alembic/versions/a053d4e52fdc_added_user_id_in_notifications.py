"""added user id in notifications

Revision ID: a053d4e52fdc
Revises: 5a476562ddbb
Create Date: 2024-11-25 15:57:39.621525

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a053d4e52fdc'
down_revision: Union[str, None] = '5a476562ddbb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('notifications', sa.Column('user_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'notifications', 'user', ['user_id'], ['id'])
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'notifications', type_='foreignkey')
    op.drop_column('notifications', 'user_id')
    # ### end Alembic commands ###