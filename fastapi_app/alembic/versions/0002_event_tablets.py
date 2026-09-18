"""Event checkout, inventory snapshots, and revocable sessions.

Revision ID: 0002
"""
from alembic import op
import sqlalchemy as sa
from app.models.user import AuthSession
from app.models.event import DinnerEvent, Consumable, RecipeLine, StockAdjustment, OrderConsumption, OrderCounter

revision = '0002'
down_revision = '0001'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    op.add_column('users', sa.Column('is_admin', sa.Boolean, nullable=False, server_default=sa.false()))
    op.execute('UPDATE users SET is_admin = is_staff')
    for model in (AuthSession, DinnerEvent, Consumable, RecipeLine, OrderCounter):
        model.__table__.create(bind, checkfirst=True)
    op.create_table('stock_adjustments',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('event_id', sa.Integer, sa.ForeignKey('dinner_events.id'), nullable=False),
        sa.Column('consumable_id', sa.Integer, sa.ForeignKey('consumables.id'), nullable=False),
        sa.Column('quantity', sa.Numeric(14, 3), nullable=False),
        sa.Column('reason', sa.String(200), nullable=False),
        sa.Column('user_id', sa.Integer, sa.ForeignKey('users.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()))
    op.create_index('ix_stock_adjustments_event_id', 'stock_adjustments', ['event_id'])
    with op.batch_alter_table('orders') as batch:
        batch.add_column(sa.Column('event_id', sa.Integer, nullable=True))
        batch.add_column(sa.Column('checkout_key', sa.String(80), nullable=True))
        batch.add_column(sa.Column('checkout_fingerprint', sa.String(64), nullable=True))
        batch.add_column(sa.Column('tickets_collected', sa.Integer, nullable=False, server_default='0'))
        batch.add_column(sa.Column('voided_at', sa.DateTime(timezone=True), nullable=True))
        batch.add_column(sa.Column('void_reason', sa.String(200), nullable=True))
        batch.create_foreign_key('fk_order_event', 'dinner_events', ['event_id'], ['id'])
        batch.create_unique_constraint('uq_order_checkout', ['user_id', 'checkout_key'])
        batch.create_index('ix_orders_event_id', ['event_id'])
    with op.batch_alter_table('order_items') as batch:
        batch.add_column(sa.Column('unit_tickets', sa.Integer, nullable=False, server_default='0'))
        batch.add_column(sa.Column('unit_value', sa.Numeric(12, 2), nullable=False, server_default='0'))
        batch.add_column(sa.Column('item_name', sa.String(100), nullable=False, server_default=''))
        batch.add_column(sa.Column('recipe_recorded', sa.Boolean, nullable=False, server_default=sa.false()))
    op.execute('UPDATE order_items SET unit_tickets = (SELECT ticket FROM food_items WHERE food_items.id = order_items.food_item_id), unit_value = (SELECT value FROM food_items WHERE food_items.id = order_items.food_item_id), item_name = (SELECT name FROM food_items WHERE food_items.id = order_items.food_item_id)')
    OrderConsumption.__table__.create(bind, checkfirst=True)
    op.execute('INSERT INTO order_counter (id, value) SELECT 1, COALESCE(MAX(display_id), 0) FROM orders')


def downgrade():
    raise RuntimeError('Event history must not be discarded; restore a verified backup for rollback')
