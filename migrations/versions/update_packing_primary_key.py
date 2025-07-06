"""update packing primary key

Revision ID: update_packing_primary_key
Revises: aa9c70c8f04d
Create Date: 2024-12-19 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'update_packing_primary_key'
down_revision = 'aa9c70c8f04d'
branch_labels = None
depends_on = None


def upgrade():
    # Drop the old unique constraint if it exists
    try:
        op.drop_constraint('uq_packing_week_product', 'packing', type_='unique')
    except:
        pass  # Constraint might not exist
    
    # Drop the old primary key if it exists (week_commencing, product_code)
    try:
        op.drop_constraint('packing_pkey', 'packing', type_='primary')
    except:
        pass  # Primary key might not exist with this name
    
    # Create the new composite primary key
    op.create_primary_key(
        'packing_pkey',
        'packing',
        ['week_commencing', 'packing_date', 'product_code', 'machinery']
    )


def downgrade():
    # Drop the new primary key
    op.drop_constraint('packing_pkey', 'packing', type_='primary')
    
    # Recreate the old unique constraint
    op.create_unique_constraint('uq_packing_week_product', 'packing', ['week_commencing', 'product_code'])
    
    # Recreate the old primary key (assuming it was just week_commencing and product_code)
    op.create_primary_key(
        'packing_pkey',
        'packing',
        ['week_commencing', 'product_code']
    ) 