"""Initial migration for user-service

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
    # Create ENUM type for user_mode
    op.execute("CREATE TYPE user_mode AS ENUM ('NIN', 'LAH')")
    
    # Create user_profiles table
    op.create_table(
        'user_profiles',
        sa.Column('profile_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('bio', sa.Text(), nullable=True),
        sa.Column('average_rating', sa.Numeric(precision=3, scale=2), nullable=True, server_default='0.00'),
        sa.Column('total_ratings', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('default_mode', postgresql.ENUM('NIN', 'LAH', name='user_mode', create_type=False), nullable=True, server_default='NIN'),
        sa.Column('phone_number', sa.String(length=20), nullable=True),
        sa.Column('profile_picture_url', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('profile_id'),
        sa.UniqueConstraint('user_id')
    )
    op.create_index(op.f('ix_user_profiles_user_id'), 'user_profiles', ['user_id'], unique=False)
    
    # Create provider_profile table
    op.create_table(
        'provider_profile',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('service_radius_miles', sa.Numeric(precision=4, scale=2), nullable=True, server_default='2.0'),
        sa.Column('vehicle_description', sa.String(length=500), nullable=True),
        sa.Column('services_offered', sa.Text(), nullable=True),
        sa.Column('hourly_rate', sa.Numeric(precision=8, scale=2), nullable=True),
        sa.Column('availability_schedule', sa.Text(), nullable=True),
        sa.Column('is_available', sa.String(length=10), nullable=True, server_default='true'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )
    op.create_index(op.f('ix_provider_profile_user_id'), 'provider_profile', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_provider_profile_user_id'), table_name='provider_profile')
    op.drop_table('provider_profile')
    op.drop_index(op.f('ix_user_profiles_user_id'), table_name='user_profiles')
    op.drop_table('user_profiles')
    op.execute('DROP TYPE user_mode')