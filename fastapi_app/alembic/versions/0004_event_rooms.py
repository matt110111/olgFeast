"""Separate event rooms, menus, kitchen queues, and stock."""
from alembic import op
import sqlalchemy as sa
revision = '0004'
down_revision = '0003'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('event_rooms',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('event_id', sa.Integer, sa.ForeignKey('dinner_events.id'), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.UniqueConstraint('event_id', 'name', name='uq_event_room_name'))
    op.create_index('ix_event_rooms_event_id', 'event_rooms', ['event_id'])
    op.create_table('room_menu_items',
        sa.Column('room_id', sa.Integer, sa.ForeignKey('event_rooms.id'), primary_key=True),
        sa.Column('food_item_id', sa.Integer, sa.ForeignKey('food_items.id'), primary_key=True))
    for table in ('orders', 'stock_adjustments'):
        with op.batch_alter_table(table) as batch:
            batch.add_column(sa.Column('room_id', sa.Integer, nullable=True))
            batch.create_foreign_key('fk_' + table + '_room', 'event_rooms', ['room_id'], ['id'])
            batch.create_index('ix_' + table + '_room_id', ['room_id'])


def downgrade():
    raise RuntimeError('Restore a verified backup to preserve room history')
