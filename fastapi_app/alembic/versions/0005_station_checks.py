"""Collect tickets once at an input station and route to multiple kitchens."""
from alembic import op
import sqlalchemy as sa

revision = '0005'
down_revision = '0004'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('station_checks',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('user_id', sa.Integer, sa.ForeignKey('users.id'), nullable=False),
        sa.Column('event_id', sa.Integer, sa.ForeignKey('dinner_events.id'), nullable=False),
        sa.Column('checkout_key', sa.String(80), nullable=False),
        sa.Column('fingerprint', sa.String(64), nullable=False),
        sa.Column('station_number', sa.Integer, nullable=False),
        sa.UniqueConstraint('user_id', 'checkout_key', name='uq_station_check'))
    with op.batch_alter_table('orders') as batch:
        batch.add_column(sa.Column('check_id', sa.Integer, nullable=True))
        batch.add_column(sa.Column('station_number', sa.Integer, nullable=True))
        batch.create_foreign_key('fk_orders_check', 'station_checks', ['check_id'], ['id'])
        batch.create_index('ix_orders_check_id', ['check_id'])


def downgrade():
    raise RuntimeError('Restore a verified backup to preserve station check history')
