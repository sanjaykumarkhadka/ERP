"""merge multiple heads

Revision ID: 7d4f834a7895
Revises: add_description_to_raw_materials, add_user_columns_and_item_master_relation, fix_raw_materials_foreign_keys, remove_raw_material_id, remove_week_commencing
Create Date: 2025-07-02 09:51:17.575250

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7d4f834a7895'
down_revision = ('add_description_to_raw_materials', 'add_user_columns_and_item_master_relation', 'fix_raw_materials_foreign_keys', 'remove_raw_material_id', 'remove_week_commencing')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
