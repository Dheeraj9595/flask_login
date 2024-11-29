"""made backref relationship with User and Bank Account

Revision ID: faf4f06cbcb7
Revises: 131cf8649c2c
Create Date: 2024-11-30 00:47:34.273829

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'faf4f06cbcb7'
down_revision: Union[str, None] = '131cf8649c2c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
