"""resolve migration cycle

Revision ID: resolve_migration_cycle
Revises: 7d4f834a7895, add_description_to_raw_materials, add_item_type_foreign_key, add_machinery_department, add_user_columns_and_item_master_relation, c73878ef2205, fix_migration_order, fix_raw_materials_foreign_keys, remove_raw_material_id, remove_week_commencing, update_packing_primary_key
Create Date: 2024-03-21

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'resolve_migration_cycle'
down_revision = ('7d4f834a7895', 'add_description_to_raw_materials', 'add_item_type_foreign_key', 
                'add_machinery_department', 'add_user_columns_and_item_master_relation', 'c73878ef2205',
                'fix_migration_order', 'fix_raw_materials_foreign_keys', 'remove_raw_material_id',
                'remove_week_commencing', 'update_packing_primary_key')
branch_labels = None
depends_on = None

def upgrade():
    pass

def downgrade():
    pass 