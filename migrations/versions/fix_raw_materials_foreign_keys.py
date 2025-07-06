"""fix raw materials foreign keys

Revision ID: fix_raw_materials_foreign_keys
Revises: aa9c70c8f04d
Create Date: 2024-03-19 11:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector

# revision identifiers, used by Alembic.
revision = 'fix_raw_materials_foreign_keys'
down_revision = 'aa9c70c8f04d'
branch_labels = None
depends_on = None

def drop_foreign_key_if_exists(table_name, fk_name):
    try:
        with op.batch_alter_table(table_name) as batch_op:
            batch_op.drop_constraint(fk_name, type_='foreignkey')
    except:
        pass

def upgrade():
    # Get database connection and inspector
    connection = op.get_bind()
    inspector = Inspector.from_engine(connection)

    # Recipe Master table changes
    if 'recipe_master' in inspector.get_table_names():
        drop_foreign_key_if_exists('recipe_master', 'fk_recipe_raw_material')
        columns = [col['name'] for col in inspector.get_columns('recipe_master')]
        with op.batch_alter_table('recipe_master') as batch_op:
            if 'raw_material' in columns:
                batch_op.drop_column('raw_material')
            if 'raw_material_id' in columns:
                batch_op.drop_column('raw_material_id')
            batch_op.add_column(sa.Column('raw_material_id', sa.Integer(), nullable=True))
            batch_op.create_foreign_key('fk_recipe_raw_material', 'raw_materials', ['raw_material_id'], ['id'])

    # Usage table changes
    if 'usage' in inspector.get_table_names():
        drop_foreign_key_if_exists('usage', 'fk_usage_raw_material')
        columns = [col['name'] for col in inspector.get_columns('usage')]
        with op.batch_alter_table('usage') as batch_op:
            if 'raw_material' in columns:
                batch_op.drop_column('raw_material')
            if 'raw_material_id' in columns:
                batch_op.drop_column('raw_material_id')
            batch_op.add_column(sa.Column('raw_material_id', sa.Integer(), nullable=True))
            batch_op.create_foreign_key('fk_usage_raw_material', 'raw_materials', ['raw_material_id'], ['id'])

    # Raw Material Report table changes
    if 'raw_material_report' in inspector.get_table_names():
        drop_foreign_key_if_exists('raw_material_report', 'fk_raw_material_report_raw_material')
        columns = [col['name'] for col in inspector.get_columns('raw_material_report')]
        with op.batch_alter_table('raw_material_report') as batch_op:
            if 'raw_material' in columns:
                batch_op.drop_column('raw_material')
            if 'raw_material_id' in columns:
                batch_op.drop_column('raw_material_id')
            batch_op.add_column(sa.Column('raw_material_id', sa.Integer(), nullable=True))
            batch_op.create_foreign_key('fk_raw_material_report_raw_material', 'raw_materials', ['raw_material_id'], ['id'])

def downgrade():
    # Recipe Master table changes
    with op.batch_alter_table('recipe_master') as batch_op:
        batch_op.drop_constraint('fk_recipe_raw_material', type_='foreignkey')
        batch_op.drop_column('raw_material_id')
        batch_op.add_column(sa.Column('raw_material', sa.String(length=200), nullable=True))

    # Usage table changes
    with op.batch_alter_table('usage') as batch_op:
        batch_op.drop_constraint('fk_usage_raw_material', type_='foreignkey')
        batch_op.drop_column('raw_material_id')
        batch_op.add_column(sa.Column('raw_material', sa.String(length=200), nullable=True))

    # Raw Material Report table changes
    with op.batch_alter_table('raw_material_report') as batch_op:
        batch_op.drop_constraint('fk_raw_material_report_raw_material', type_='foreignkey')
        batch_op.drop_column('raw_material_id')
        batch_op.add_column(sa.Column('raw_material', sa.String(length=200), nullable=True)) 