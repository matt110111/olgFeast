"""Hold guest orders until a volunteer confirms physical tickets."""
from alembic import op
import sqlalchemy as sa
revision = '0003'
down_revision = '0002'
branch_labels = None
depends_on = None

def upgrade():
    with op.batch_alter_table('orders') as batch:
        batch.add_column(sa.Column('awaiting_tickets', sa.Boolean, nullable=False, server_default=sa.false()))
        batch.add_column(sa.Column('tickets_confirmed_by', sa.Integer, nullable=True))
        batch.add_column(sa.Column('tickets_confirmed_at', sa.DateTime(timezone=True), nullable=True))
        batch.create_foreign_key('fk_order_ticket_collector', 'users', ['tickets_confirmed_by'], ['id'])

def downgrade():
    raise RuntimeError('Restore a verified backup to preserve ticket confirmation history')
