"""Baseline for new databases and installations previously created with create_all.

Revision ID: 0001
"""
from alembic import op
import sqlalchemy as sa

revision = '0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    if not sa.inspect(bind).has_table('users'):
        metadata = sa.MetaData()
        def times():
            return [sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
                    sa.Column('updated_at', sa.DateTime(timezone=True))]
        sa.Table('users', metadata, sa.Column('id', sa.Integer, primary_key=True),
            sa.Column('username', sa.String(150), nullable=False, unique=True),
            sa.Column('email', sa.String(255), nullable=False, unique=True),
            sa.Column('hashed_password', sa.String(255), nullable=False),
            sa.Column('is_active', sa.Boolean), sa.Column('is_staff', sa.Boolean), *times())
        sa.Table('profiles', metadata, sa.Column('id', sa.Integer, primary_key=True),
            sa.Column('user_id', sa.Integer, sa.ForeignKey('users.id'), nullable=False, unique=True),
            sa.Column('full_name', sa.String(255)), sa.Column('phone', sa.String(20)), *times())
        sa.Table('food_items', metadata, sa.Column('id', sa.Integer, primary_key=True),
            sa.Column('food_group', sa.String(40), nullable=False), sa.Column('name', sa.String(40), nullable=False),
            sa.Column('value', sa.Float), sa.Column('ticket', sa.Integer), sa.Column('description', sa.String(500)),
            sa.Column('is_available', sa.String(10)), *times())
        sa.Table('carts', metadata, sa.Column('id', sa.Integer, primary_key=True),
            sa.Column('user_id', sa.Integer, sa.ForeignKey('users.id'), nullable=False, unique=True), *times())
        sa.Table('cart_items', metadata, sa.Column('id', sa.Integer, primary_key=True),
            sa.Column('cart_id', sa.Integer, sa.ForeignKey('carts.id'), nullable=False),
            sa.Column('food_item_id', sa.Integer, sa.ForeignKey('food_items.id'), nullable=False),
            sa.Column('quantity', sa.Integer, nullable=False), *times())
        sa.Table('orders', metadata, sa.Column('id', sa.Integer, primary_key=True),
            sa.Column('display_id', sa.Integer, nullable=False, unique=True),
            sa.Column('ref_code', sa.String(40), nullable=False, unique=True),
            sa.Column('user_id', sa.Integer, sa.ForeignKey('users.id'), nullable=False),
            sa.Column('customer_name', sa.String(100), nullable=False),
            sa.Column('status', sa.Enum('PENDING', 'PREPARING', 'READY', 'COMPLETE', name='orderstatus'), nullable=False),
            sa.Column('date_ordered', sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column('date_preparing', sa.DateTime(timezone=True)), sa.Column('date_ready', sa.DateTime(timezone=True)),
            sa.Column('date_complete', sa.DateTime(timezone=True)),
            sa.Column('last_status_change', sa.DateTime(timezone=True), server_default=sa.func.now()))
        sa.Table('order_items', metadata, sa.Column('id', sa.Integer, primary_key=True),
            sa.Column('order_id', sa.Integer, sa.ForeignKey('orders.id'), nullable=False),
            sa.Column('food_item_id', sa.Integer, sa.ForeignKey('food_items.id'), nullable=False),
            sa.Column('quantity', sa.Integer, nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()))
        metadata.create_all(bind)
    elif 'display_id' not in {c['name'] for c in sa.inspect(bind).get_columns('orders')}:
        op.add_column('orders', sa.Column('display_id', sa.Integer, nullable=True))
        op.execute('UPDATE orders SET display_id = id')
        with op.batch_alter_table('orders') as batch:
            batch.alter_column('display_id', nullable=False, existing_type=sa.Integer())
            batch.create_unique_constraint('uq_orders_display_id', ['display_id'])


def downgrade():
    raise RuntimeError('Restore a verified database backup to roll back the baseline')
