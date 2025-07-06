"""rename raw_material table

Revision ID: rename_raw_material_table
Revises: 
Create Date: 2024-03-19

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'rename_raw_material_table'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Rename the table
    op.rename_table('raw_material', 'raw_material_report')

def downgrade():
    # Revert the rename
    op.rename_table('raw_material_report', 'raw_material') 