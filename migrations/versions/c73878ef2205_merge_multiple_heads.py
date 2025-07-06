"""merge multiple heads

Revision ID: c73878ef2205
Revises: 7d4f834a7895, add_machinery_department, fix_migration_order
Create Date: 2025-07-02 13:28:10.742594

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c73878ef2205'
down_revision = ('7d4f834a7895', 'add_machinery_department', 'fix_migration_order')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
