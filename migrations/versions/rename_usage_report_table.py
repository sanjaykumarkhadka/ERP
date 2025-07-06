"""rename usage_report table

Revision ID: rename_usage_report_table
Revises: aa9c70c8f04d
Create Date: 2024-03-21

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'rename_usage_report_table'
down_revision = 'aa9c70c8f04d'
branch_labels = None
depends_on = None

def upgrade():
    # Rename table
    op.rename_table('usage_report', 'usage_report_table')

def downgrade():
    # Revert table name
    op.rename_table('usage_report_table', 'usage_report') 