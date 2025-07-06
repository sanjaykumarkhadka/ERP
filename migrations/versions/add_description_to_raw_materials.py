"""Add description column to raw_materials table

Revision ID: add_description_to_raw_materials
Revises: 
Create Date: 2024-03-21

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_description_to_raw_materials'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Add description column to raw_materials table
    op.add_column('raw_materials',
        sa.Column('description', sa.String(255), nullable=True)
    )

def downgrade():
    # Remove description column from raw_materials table
    op.drop_column('raw_materials', 'description') 