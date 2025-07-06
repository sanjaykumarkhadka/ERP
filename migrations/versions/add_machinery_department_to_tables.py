"""Add machinery and department to tables

Revision ID: add_machinery_department
Revises: 7d4f834a7895
Create Date: 2024-03-21

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_machinery_department'
down_revision = '7d4f834a7895'
branch_labels = None
depends_on = None

def upgrade():
    # Add columns to SOH table
    with op.batch_alter_table('soh') as batch_op:
        batch_op.add_column(sa.Column('machinery_id', sa.Integer, nullable=True))
        batch_op.add_column(sa.Column('department_id', sa.Integer, nullable=True))
        batch_op.create_foreign_key('fk_soh_machinery', 'machinery', ['machinery_id'], ['machineID'], ondelete='SET NULL')
        batch_op.create_foreign_key('fk_soh_department', 'department', ['department_id'], ['department_id'], ondelete='SET NULL')

    # Add columns to Filling table
    with op.batch_alter_table('filling') as batch_op:
        batch_op.add_column(sa.Column('machinery_id', sa.Integer, nullable=True))
        batch_op.add_column(sa.Column('department_id', sa.Integer, nullable=True))
        batch_op.create_foreign_key('fk_filling_machinery', 'machinery', ['machinery_id'], ['machineID'], ondelete='SET NULL')
        batch_op.create_foreign_key('fk_filling_department', 'department', ['department_id'], ['department_id'], ondelete='SET NULL')

    # Update Packing table (already has machinery column)
    with op.batch_alter_table('packing') as batch_op:
        # First drop the old foreign key if it exists
        try:
            batch_op.drop_constraint('packing_ibfk_1', type_='foreignkey')
        except:
            pass
        
        # Add department column
        batch_op.add_column(sa.Column('department_id', sa.Integer, nullable=True))
        batch_op.create_foreign_key('fk_packing_department', 'department', ['department_id'], ['department_id'], ondelete='SET NULL')
        
        # Rename machinery to machinery_id and recreate foreign key
        batch_op.alter_column('machinery', 
                            new_column_name='machinery_id',
                            existing_type=sa.Integer,
                            nullable=True)
        batch_op.create_foreign_key('fk_packing_machinery', 'machinery', ['machinery_id'], ['machineID'], ondelete='SET NULL')

    # Add columns to Production table
    with op.batch_alter_table('production') as batch_op:
        batch_op.add_column(sa.Column('machinery_id', sa.Integer, nullable=True))
        batch_op.add_column(sa.Column('department_id', sa.Integer, nullable=True))
        batch_op.create_foreign_key('fk_production_machinery', 'machinery', ['machinery_id'], ['machineID'], ondelete='SET NULL')
        batch_op.create_foreign_key('fk_production_department', 'department', ['department_id'], ['department_id'], ondelete='SET NULL')

def downgrade():
    # Remove from SOH table
    with op.batch_alter_table('soh') as batch_op:
        batch_op.drop_constraint('fk_soh_machinery', type_='foreignkey')
        batch_op.drop_constraint('fk_soh_department', type_='foreignkey')
        batch_op.drop_column('machinery_id')
        batch_op.drop_column('department_id')

    # Remove from Filling table
    with op.batch_alter_table('filling') as batch_op:
        batch_op.drop_constraint('fk_filling_machinery', type_='foreignkey')
        batch_op.drop_constraint('fk_filling_department', type_='foreignkey')
        batch_op.drop_column('machinery_id')
        batch_op.drop_column('department_id')

    # Revert Packing table
    with op.batch_alter_table('packing') as batch_op:
        batch_op.drop_constraint('fk_packing_machinery', type_='foreignkey')
        batch_op.drop_constraint('fk_packing_department', type_='foreignkey')
        batch_op.alter_column('machinery_id', 
                            new_column_name='machinery',
                            existing_type=sa.Integer,
                            nullable=True)
        batch_op.drop_column('department_id')

    # Remove from Production table
    with op.batch_alter_table('production') as batch_op:
        batch_op.drop_constraint('fk_production_machinery', type_='foreignkey')
        batch_op.drop_constraint('fk_production_department', type_='foreignkey')
        batch_op.drop_column('machinery_id')
        batch_op.drop_column('department_id') 