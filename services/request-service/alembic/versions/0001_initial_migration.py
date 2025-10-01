"""Initial migration for request-service

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
    # Create ENUM types
    op.execute("CREATE TYPE servicerequestatus AS ENUM ('PENDING', 'ACCEPTED', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED')")
    op.execute("CREATE TYPE assignmentstatus AS ENUM ('ASSIGNED', 'ACCEPTED', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED')")
    op.execute("CREATE TYPE servicetype AS ENUM ('TRANSPORTATION', 'ERRANDS', 'OTHER')")
    op.execute("CREATE TYPE paymentstatus AS ENUM ('UNPAID', 'PAID', 'PAYMENT_FAILED')")
    
    # Create service_requests table
    op.create_table(
        'service_requests',
        sa.Column('request_id', sa.String(length=36), nullable=False),
        sa.Column('requester_id', sa.String(length=36), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('service_type', sa.Enum('TRANSPORTATION', 'ERRANDS', 'OTHER', name='servicetype'), nullable=False),
        sa.Column('pickup_latitude', sa.Float(), nullable=False),
        sa.Column('pickup_longitude', sa.Float(), nullable=False),
        sa.Column('destination_latitude', sa.Float(), nullable=True),
        sa.Column('destination_longitude', sa.Float(), nullable=True),
        sa.Column('offered_amount', sa.Float(), nullable=True),
        sa.Column('status', sa.Enum('PENDING', 'ACCEPTED', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED', name='servicerequestatus'), nullable=True),
        sa.Column('payment_status', sa.Enum('UNPAID', 'PAID', 'PAYMENT_FAILED', name='paymentstatus'), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('request_id')
    )
    
    # Create service_assignments table
    op.create_table(
        'service_assignments',
        sa.Column('assignment_id', sa.String(length=36), nullable=False),
        sa.Column('request_id', sa.String(length=36), nullable=False),
        sa.Column('provider_id', sa.String(length=36), nullable=False),
        sa.Column('status', sa.Enum('ASSIGNED', 'ACCEPTED', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED', name='assignmentstatus'), nullable=True),
        sa.Column('provider_notes', sa.Text(), nullable=True),
        sa.Column('completion_notes', sa.Text(), nullable=True),
        sa.Column('estimated_completion_time', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['request_id'], ['service_requests.request_id'], ),
        sa.PrimaryKeyConstraint('assignment_id')
    )
    
    # Create ratings table
    op.create_table(
        'ratings',
        sa.Column('rating_id', sa.String(length=36), nullable=False),
        sa.Column('assignment_id', sa.String(length=36), nullable=False),
        sa.Column('rater_id', sa.String(length=36), nullable=False),
        sa.Column('ratee_id', sa.String(length=36), nullable=False),
        sa.Column('rating_score', sa.Integer(), nullable=False),
        sa.Column('review_text', sa.Text(), nullable=True),
        sa.Column('is_provider_rating', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['assignment_id'], ['service_assignments.assignment_id'], ),
        sa.PrimaryKeyConstraint('rating_id')
    )


def downgrade() -> None:
    op.drop_table('ratings')
    op.drop_table('service_assignments')
    op.drop_table('service_requests')
    op.execute('DROP TYPE paymentstatus')
    op.execute('DROP TYPE servicetype')
    op.execute('DROP TYPE assignmentstatus')
    op.execute('DROP TYPE servicerequestatus')


