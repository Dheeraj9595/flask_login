from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'b5684cf94448'
down_revision = 'a053d4e52fdc'
branch_labels = None
depends_on = None

def upgrade():
    with op.batch_alter_table("notifications", schema=None) as batch_op:
        batch_op.add_column(sa.Column('user_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            'fk_user_id', 'user', ['user_id'], ['id']
        )

def downgrade():
    with op.batch_alter_table("notifications", schema=None) as batch_op:
        batch_op.drop_constraint('fk_user_id', type_='foreignkey')
        batch_op.drop_column('user_id')
