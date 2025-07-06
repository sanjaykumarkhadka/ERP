"""remove temp columns from item master

Revision ID: remove_temp_columns
Revises: aa9c70c8f04d
Create Date: 2024-03-21

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'remove_temp_columns'
down_revision = 'aa9c70c8f04d'
branch_labels = None
depends_on = None

def upgrade():
    # Drop the temporary columns
    with op.batch_alter_table('item_master') as batch_op:
        batch_op.drop_column('product_description')
        batch_op.drop_column('filling_code')
        batch_op.drop_column('production_code')

def downgrade():
    # Add back the columns if needed to rollback
    with op.batch_alter_table('item_master') as batch_op:
        batch_op.add_column(sa.Column('product_description', sa.String(255), nullable=True))
        batch_op.add_column(sa.Column('filling_code', sa.String(50), nullable=True))
        batch_op.add_column(sa.Column('production_code', sa.String(50), nullable=True)) 