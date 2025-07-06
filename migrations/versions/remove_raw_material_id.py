"""remove raw_material_id column

Revision ID: remove_raw_material_id
Revises: 
Create Date: 2024-03-19

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'remove_raw_material_id'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Drop the raw_material_id column from usage_report table
    op.drop_column('usage_report', 'raw_material_id')

def downgrade():
    # Add back the raw_material_id column if needed
    op.add_column('usage_report', sa.Column('raw_material_id', sa.Integer(), nullable=True)) 