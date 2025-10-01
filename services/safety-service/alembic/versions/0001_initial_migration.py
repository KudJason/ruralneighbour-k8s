"""Initial migration for safety-service

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
    # Create safety_reports table
    op.create_table(
        'safety_reports',
        sa.Column('report_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('reporter_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('reported_user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('service_assignment_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('incident_type', sa.String(length=50), nullable=False),
        sa.Column('incident_severity', sa.String(length=50), nullable=True, server_default='medium'),
        sa.Column('incident_description', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=True, server_default='reported'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('report_id')
    )
    
    # Create disputes table
    op.create_table(
        'disputes',
        sa.Column('dispute_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('service_assignment_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('complainant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('respondent_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('dispute_type', sa.String(length=50), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=True, server_default='open'),
        sa.Column('resolution_notes', sa.Text(), nullable=True),
        sa.Column('resolved_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('dispute_id')
    )
    
    # Create platform_metrics table
    op.create_table(
        'platform_metrics',
        sa.Column('metric_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('metric_name', sa.String(length=100), nullable=False),
        sa.Column('metric_value', sa.Numeric(precision=15, scale=4), nullable=False),
        sa.Column('measurement_date', sa.Date(), nullable=False),
        sa.Column('measurement_period', sa.String(length=50), nullable=True, server_default='daily'),
        sa.PrimaryKeyConstraint('metric_id')
    )


def downgrade() -> None:
    op.drop_table('platform_metrics')
    op.drop_table('disputes')
    op.drop_table('safety_reports')


