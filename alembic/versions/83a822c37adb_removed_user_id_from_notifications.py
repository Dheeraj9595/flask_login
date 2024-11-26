"""removed user_id from notifications

Revision ID: 83a822c37adb
Revises: 4f40cbbdb175
Create Date: 2024-11-25 15:48:42.800424

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '83a822c37adb'
down_revision: Union[str, None] = '4f40cbbdb175'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
