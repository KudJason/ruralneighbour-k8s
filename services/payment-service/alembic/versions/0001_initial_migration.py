"""Initial migration for payment-service

Revision ID: 0001
Revises: 
Create Date: 2025-09-30 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create payments table
    op.create_table(
        'payments',
        sa.Column('payment_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('request_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('payer_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('payee_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('amount', sa.DECIMAL(precision=10, scale=2), nullable=False),
        sa.Column('payment_status', sa.String(length=50), nullable=True, server_default='pending'),
        sa.Column('payment_method', sa.String(length=50), nullable=False),
        sa.Column('transaction_id', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('payment_id')
    )
    
    # Create payment_history table
    op.create_table(
        'payment_history',
        sa.Column('history_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('payment_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['payment_id'], ['payments.payment_id'], ),
        sa.PrimaryKeyConstraint('history_id')
    )
    
    # Create refunds table
    op.create_table(
        'refunds',
        sa.Column('refund_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('payment_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('amount', sa.DECIMAL(precision=10, scale=2), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=True, server_default='pending'),
        sa.Column('refund_reason', sa.Text(), nullable=False),
        sa.Column('approved_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('completed_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['payment_id'], ['payments.payment_id'], ),
        sa.PrimaryKeyConstraint('refund_id')
    )
    
    # Create user_payment_methods table
    op.create_table(
        'user_payment_methods',
        sa.Column('method_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('method_type', sa.String(length=50), nullable=False),
        sa.Column('provider', sa.String(length=50), nullable=False),
        sa.Column('provider_method_id', sa.String(length=255), nullable=False),
        sa.Column('display_name', sa.String(length=100), nullable=True),
        sa.Column('last_four', sa.String(length=4), nullable=True),
        sa.Column('brand', sa.String(length=50), nullable=True),
        sa.Column('expiry_month', sa.Integer(), nullable=True),
        sa.Column('expiry_year', sa.Integer(), nullable=True),
        sa.Column('is_default', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.CheckConstraint('NOT (is_default = true AND is_active = false)', name='default_must_be_active'),
        sa.PrimaryKeyConstraint('method_id')
    )
    
    # Create payment_method_usage table
    op.create_table(
        'payment_method_usage',
        sa.Column('usage_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('method_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('payment_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('used_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['method_id'], ['user_payment_methods.method_id'], ),
        sa.ForeignKeyConstraint(['payment_id'], ['payments.payment_id'], ),
        sa.PrimaryKeyConstraint('usage_id')
    )


def downgrade() -> None:
    op.drop_table('payment_method_usage')
    op.drop_table('user_payment_methods')
    op.drop_table('refunds')
    op.drop_table('payment_history')
    op.drop_table('payments')


