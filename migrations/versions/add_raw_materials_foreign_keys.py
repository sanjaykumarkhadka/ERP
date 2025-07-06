"""add raw materials foreign keys

Revision ID: add_raw_materials_foreign_keys
Revises: create_raw_materials_table
Create Date: 2024-03-19 10:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'add_raw_materials_foreign_keys'
down_revision = 'create_raw_materials_table'
branch_labels = None
depends_on = None


def upgrade():
    # Recipe Master table changes
    with op.batch_alter_table('recipe_master') as batch_op:
        # First create the new column
        batch_op.add_column(sa.Column('raw_material_id', sa.Integer(), nullable=True))
        # Add foreign key constraint
        batch_op.create_foreign_key('fk_recipe_raw_material', 'raw_materials', ['raw_material_id'], ['id'])
        # Drop the old column
        batch_op.drop_column('raw_material')

    # Usage table changes
    with op.batch_alter_table('usage') as batch_op:
        # First create the new column
        batch_op.add_column(sa.Column('raw_material_id', sa.Integer(), nullable=True))
        # Add foreign key constraint
        batch_op.create_foreign_key('fk_usage_raw_material', 'raw_materials', ['raw_material_id'], ['id'])
        # Drop the old column
        batch_op.drop_column('raw_material')

    # Raw Material Report table changes
    with op.batch_alter_table('raw_material_report') as batch_op:
        # First create the new column
        batch_op.add_column(sa.Column('raw_material_id', sa.Integer(), nullable=True))
        # Add foreign key constraint
        batch_op.create_foreign_key('fk_raw_material_report_raw_material', 'raw_materials', ['raw_material_id'], ['id'])
        # Drop the old column
        batch_op.drop_column('raw_material')


def downgrade():
    # Recipe Master table changes
    with op.batch_alter_table('recipe_master') as batch_op:
        batch_op.add_column(sa.Column('raw_material', sa.String(length=200), nullable=True))
        batch_op.drop_constraint('fk_recipe_raw_material', type_='foreignkey')
        batch_op.drop_column('raw_material_id')

    # Usage table changes
    with op.batch_alter_table('usage') as batch_op:
        batch_op.add_column(sa.Column('raw_material', sa.String(length=255), nullable=True))
        batch_op.drop_constraint('fk_usage_raw_material', type_='foreignkey')
        batch_op.drop_column('raw_material_id')

    # Raw Material Report table changes
    with op.batch_alter_table('raw_material_report') as batch_op:
        batch_op.add_column(sa.Column('raw_material', sa.String(length=255), nullable=True))
        batch_op.drop_constraint('fk_raw_material_report_raw_material', type_='foreignkey')
        batch_op.drop_column('raw_material_id') 