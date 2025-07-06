"""Fix migration order

Revision ID: fix_migration_order
Revises: fd8a82f13f08
Create Date: 2024-03-21

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime, timedelta

# revision identifiers, used by Alembic.
revision = 'fix_migration_order'
down_revision = 'fd8a82f13f08'
branch_labels = None
depends_on = None

def upgrade():
    # Create tables only if they don't exist
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    existing_tables = inspector.get_table_names()

    # Step 1: Create raw_materials table if it doesn't exist
    if 'raw_materials' not in existing_tables:
        op.create_table('raw_materials',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('raw_material', sa.String(length=255), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('raw_material')
        )

    # Step 2: Create raw_material_report table if it doesn't exist
    if 'raw_material_report' not in existing_tables:
        op.create_table('raw_material_report',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('production_date', sa.Date(), nullable=False),
            sa.Column('week_commencing', sa.Date(), nullable=False),
            sa.Column('raw_material', sa.String(length=255), nullable=False),
            sa.Column('raw_material_id', sa.Integer(), nullable=True),
            sa.Column('meat_required', sa.Float(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['raw_material_id'], ['raw_materials.id'], ondelete='SET NULL'),
            sa.PrimaryKeyConstraint('id')
        )

    # Step 3: Add user columns if they don't exist
    users_columns = [c['name'] for c in inspector.get_columns('users')]
    if 'department_id' not in users_columns:
        op.add_column('users', sa.Column('department_id', sa.Integer(), nullable=True))
    if 'mobile' not in users_columns:
        op.add_column('users', sa.Column('mobile', sa.String(20), nullable=True))
    if 'start_date' not in users_columns:
        op.add_column('users', sa.Column('start_date', sa.Date(), nullable=True))
    
    # Step 4: Add foreign key constraint for department_id if it doesn't exist
    users_fks = inspector.get_foreign_keys('users')
    if not any(fk['name'] == 'fk_users_department' for fk in users_fks):
        op.create_foreign_key(
            'fk_users_department',
            'users', 'department',
            ['department_id'], ['department_id'],
            onupdate='CASCADE', ondelete='SET NULL'
        )
    
    # Step 5: Add created_by and updated_by columns to item_master if they don't exist
    item_master_columns = [c['name'] for c in inspector.get_columns('item_master')]
    if 'created_by_id' not in item_master_columns:
        op.add_column('item_master', sa.Column('created_by_id', sa.Integer(), nullable=True))
    if 'updated_by_id' not in item_master_columns:
        op.add_column('item_master', sa.Column('updated_by_id', sa.Integer(), nullable=True))
    
    # Step 6: Add foreign key constraints for created_by and updated_by if they don't exist
    item_master_fks = inspector.get_foreign_keys('item_master')
    if not any(fk['name'] == 'fk_item_master_created_by' for fk in item_master_fks):
        op.create_foreign_key(
            'fk_item_master_created_by',
            'item_master', 'users',
            ['created_by_id'], ['id'],
            onupdate='CASCADE', ondelete='SET NULL'
        )
    if not any(fk['name'] == 'fk_item_master_updated_by' for fk in item_master_fks):
        op.create_foreign_key(
            'fk_item_master_updated_by',
            'item_master', 'users',
            ['updated_by_id'], ['id'],
            onupdate='CASCADE', ondelete='SET NULL'
        )

    # Step 7: Remove week_commencing from recipe_master if it exists
    recipe_master_columns = [c['name'] for c in inspector.get_columns('recipe_master')]
    if 'week_commencing' in recipe_master_columns:
        op.drop_column('recipe_master', 'week_commencing')

def downgrade():
    # Step 1: Add week_commencing back to recipe_master
    op.add_column('recipe_master', sa.Column('week_commencing', sa.Date(), nullable=True))
    
    # Step 2: Remove foreign key constraints from item_master
    op.drop_constraint('fk_item_master_updated_by', 'item_master', type_='foreignkey')
    op.drop_constraint('fk_item_master_created_by', 'item_master', type_='foreignkey')
    
    # Step 3: Remove columns from item_master
    op.drop_column('item_master', 'updated_by_id')
    op.drop_column('item_master', 'created_by_id')
    
    # Step 4: Remove foreign key constraint from users
    op.drop_constraint('fk_users_department', 'users', type_='foreignkey')
    
    # Step 5: Remove columns from users
    op.drop_column('users', 'start_date')
    op.drop_column('users', 'mobile')
    op.drop_column('users', 'department_id')
    
    # Step 6: Drop raw_material_report table
    op.drop_table('raw_material_report')
    
    # Step 7: Drop raw_materials table
    op.drop_table('raw_materials') 