"""Remove week_commencing from recipe_master

Revision ID: remove_week_commencing
Revises: fd8a82f13f08
Create Date: 2024-03-14 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime, timedelta

# revision identifiers, used by Alembic
revision = 'remove_week_commencing'
down_revision = 'fd8a82f13f08'
branch_labels = None
depends_on = None

def upgrade():
    # Before removing the column, we need to ensure the raw_material_report table 
    # has all the necessary data
    
    # First, copy any week_commencing data that might be needed
    op.execute("""
        INSERT INTO raw_material_report (
            production_date,
            week_commencing,
            raw_material,
            raw_material_id,
            meat_required,
            created_at
        )
        SELECT DISTINCT
            r.week_commencing as production_date,
            r.week_commencing,
            rm.raw_material,
            rm.id as raw_material_id,
            r.kg_per_batch * r.percentage / 100 as meat_required,
            NOW() as created_at
        FROM recipe_master r
        JOIN raw_materials rm ON r.raw_material_id = rm.id
        WHERE r.week_commencing IS NOT NULL
        AND NOT EXISTS (
            SELECT 1 
            FROM raw_material_report rr 
            WHERE rr.week_commencing = r.week_commencing
            AND rr.raw_material_id = rm.id
        )
    """)
    
    # Now we can safely remove the column
    op.drop_column('recipe_master', 'week_commencing')

def downgrade():
    # Add the column back
    op.add_column('recipe_master', sa.Column('week_commencing', sa.Date(), nullable=True))
    
    # Set a default value (current date's Monday) for existing records
    today = datetime.now().date()
    monday = today - timedelta(days=today.weekday())
    op.execute(f"UPDATE recipe_master SET week_commencing = '{monday}' WHERE week_commencing IS NULL")
    
    # Make it not nullable
    op.alter_column('recipe_master', 'week_commencing',
               existing_type=sa.Date(),
               nullable=False) 