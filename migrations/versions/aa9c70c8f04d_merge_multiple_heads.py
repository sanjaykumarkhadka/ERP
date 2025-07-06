"""merge multiple heads

Revision ID: aa9c70c8f04d
Revises: add_raw_materials_foreign_keys, fd8a82f13f08
Create Date: 2025-06-10 05:09:29.663147

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'aa9c70c8f04d'
down_revision = ('add_raw_materials_foreign_keys', 'fd8a82f13f08')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
