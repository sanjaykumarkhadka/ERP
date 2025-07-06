"""Add user columns and item master relation

Revision ID: add_user_columns_and_item_master_relation
Revises: add_item_type_foreign_key
Create Date: 2024-03-21

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime

# revision identifiers, used by Alembic.
revision = 'add_user_columns_and_item_master_relation'
down_revision = 'add_item_type_foreign_key'
branch_labels = None
depends_on = None

def upgrade():
    # Add new columns to users table
    op.add_column('users', sa.Column('department_id', sa.Integer(), nullable=True))
    op.add_column('users', sa.Column('mobile', sa.String(20), nullable=True))
    op.add_column('users', sa.Column('start_date', sa.Date(), nullable=True))
    
    # Add foreign key constraint for department_id
    op.create_foreign_key(
        'fk_users_department',
        'users', 'department',
        ['department_id'], ['department_id'],
        onupdate='CASCADE', ondelete='SET NULL'
    )
    
    # Add created_by and updated_by columns to item_master
    op.add_column('item_master', sa.Column('created_by_id', sa.Integer(), nullable=True))
    op.add_column('item_master', sa.Column('updated_by_id', sa.Integer(), nullable=True))
    
    # Add foreign key constraints for created_by and updated_by
    op.create_foreign_key(
        'fk_item_master_created_by',
        'item_master', 'users',
        ['created_by_id'], ['id'],
        onupdate='CASCADE', ondelete='SET NULL'
    )
    op.create_foreign_key(
        'fk_item_master_updated_by',
        'item_master', 'users',
        ['updated_by_id'], ['id'],
        onupdate='CASCADE', ondelete='SET NULL'
    )

def downgrade():
    # Remove foreign key constraints first
    op.drop_constraint('fk_item_master_updated_by', 'item_master', type_='foreignkey')
    op.drop_constraint('fk_item_master_created_by', 'item_master', type_='foreignkey')
    op.drop_constraint('fk_users_department', 'users', type_='foreignkey')
    
    # Remove columns from item_master
    op.drop_column('item_master', 'updated_by_id')
    op.drop_column('item_master', 'created_by_id')
    
    # Remove columns from users
    op.drop_column('users', 'start_date')
    op.drop_column('users', 'mobile')
    op.drop_column('users', 'department_id') 