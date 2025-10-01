"""Initial migration for location-service

Revision ID: 0001
Revises: 
Create Date: 2025-09-30 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import geoalchemy2

# revision identifiers, used by Alembic.
revision = '0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enable PostGIS extension
    op.execute('CREATE EXTENSION IF NOT EXISTS postgis')
    
    # Create user_addresses table
    op.create_table(
        'user_addresses',
        sa.Column('address_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('street_address', sa.String(length=255), nullable=False),
        sa.Column('city', sa.String(length=100), nullable=False),
        sa.Column('state', sa.String(length=50), nullable=False),
        sa.Column('postal_code', sa.String(length=20), nullable=False),
        sa.Column('country', sa.String(length=100), nullable=False, server_default='USA'),
        sa.Column('location', geoalchemy2.types.Geography(geometry_type='POINT', srid=4326, from_text='ST_GeogFromText', name='geography'), nullable=False),
        sa.Column('is_within_service_area', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('is_primary', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('address_type', sa.String(length=50), nullable=True, server_default='residential'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('address_id')
    )
    
    # Create saved_locations table
    op.create_table(
        'saved_locations',
        sa.Column('location_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('address', sa.String(length=255), nullable=False),
        sa.Column('latitude', sa.String(length=50), nullable=False),
        sa.Column('longitude', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('location_id')
    )


def downgrade() -> None:
    op.drop_table('saved_locations')
    op.drop_table('user_addresses')
    op.execute('DROP EXTENSION IF EXISTS postgis')


