"""Add display_id to orders

Revision ID: 0001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add display_id column to orders table
    op.add_column('orders', sa.Column('display_id', sa.Integer(), nullable=False))
    
    # Populate existing orders with display_id values starting from 1
    connection = op.get_bind()
    result = connection.execute(sa.text("SELECT id FROM orders ORDER BY id"))
    orders = result.fetchall()
    
    for i, (order_id,) in enumerate(orders, 1):
        connection.execute(
            sa.text("UPDATE orders SET display_id = :display_id WHERE id = :order_id"),
            {"display_id": i, "order_id": order_id}
        )
    
    # Create unique index on display_id
    op.create_unique_constraint('uq_orders_display_id', 'orders', ['display_id'])


def downgrade() -> None:
    # Drop the unique constraint and column
    op.drop_constraint('uq_orders_display_id', 'orders', type_='unique')
    op.drop_column('orders', 'display_id')
