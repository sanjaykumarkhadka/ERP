"""Add machinery and department relations

Revision ID: add_machinery_department_relations
Revises: resolve_migration_cycle
Create Date: 2024-03-21

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_machinery_department_relations'
down_revision = 'resolve_migration_cycle'
branch_labels = None
depends_on = None

def upgrade():
    # Add machinery_id and department_id to SOH
    op.execute("""
        ALTER TABLE soh 
        ADD COLUMN machinery_id INT NULL,
        ADD COLUMN department_id INT NULL,
        ADD CONSTRAINT fk_soh_machinery FOREIGN KEY (machinery_id) REFERENCES machinery(machineID) ON DELETE SET NULL,
        ADD CONSTRAINT fk_soh_department FOREIGN KEY (department_id) REFERENCES department(department_id) ON DELETE SET NULL
    """)

    # Add machinery_id and department_id to Filling
    op.execute("""
        ALTER TABLE filling 
        ADD COLUMN machinery_id INT NULL,
        ADD COLUMN department_id INT NULL,
        ADD CONSTRAINT fk_filling_machinery FOREIGN KEY (machinery_id) REFERENCES machinery(machineID) ON DELETE SET NULL,
        ADD CONSTRAINT fk_filling_department FOREIGN KEY (department_id) REFERENCES department(department_id) ON DELETE SET NULL
    """)

    # Update Packing table (already has machinery column)
    op.execute("""
        ALTER TABLE packing 
        ADD COLUMN department_id INT NULL,
        CHANGE COLUMN machinery machinery_id INT NULL,
        ADD CONSTRAINT fk_packing_machinery FOREIGN KEY (machinery_id) REFERENCES machinery(machineID) ON DELETE SET NULL,
        ADD CONSTRAINT fk_packing_department FOREIGN KEY (department_id) REFERENCES department(department_id) ON DELETE SET NULL
    """)

    # Add machinery_id and department_id to Production
    op.execute("""
        ALTER TABLE production 
        ADD COLUMN machinery_id INT NULL,
        ADD COLUMN department_id INT NULL,
        ADD CONSTRAINT fk_production_machinery FOREIGN KEY (machinery_id) REFERENCES machinery(machineID) ON DELETE SET NULL,
        ADD CONSTRAINT fk_production_department FOREIGN KEY (department_id) REFERENCES department(department_id) ON DELETE SET NULL
    """)

def downgrade():
    # Remove from SOH
    op.execute("""
        ALTER TABLE soh 
        DROP FOREIGN KEY fk_soh_machinery,
        DROP FOREIGN KEY fk_soh_department,
        DROP COLUMN machinery_id,
        DROP COLUMN department_id
    """)

    # Remove from Filling
    op.execute("""
        ALTER TABLE filling 
        DROP FOREIGN KEY fk_filling_machinery,
        DROP FOREIGN KEY fk_filling_department,
        DROP COLUMN machinery_id,
        DROP COLUMN department_id
    """)

    # Revert Packing
    op.execute("""
        ALTER TABLE packing 
        DROP FOREIGN KEY fk_packing_machinery,
        DROP FOREIGN KEY fk_packing_department,
        CHANGE COLUMN machinery_id machinery INT NULL,
        DROP COLUMN department_id
    """)

    # Remove from Production
    op.execute("""
        ALTER TABLE production 
        DROP FOREIGN KEY fk_production_machinery,
        DROP FOREIGN KEY fk_production_department,
        DROP COLUMN machinery_id,
        DROP COLUMN department_id
    """) 