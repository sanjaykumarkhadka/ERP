"""Add item_type_id foreign key to item_master table

Revision ID: add_item_type_foreign_key
Revises: update_packing_primary_key
Create Date: 2024-12-19 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_item_type_foreign_key'
down_revision = 'update_packing_primary_key'
branch_labels = None
depends_on = None

def upgrade():
    # Step 1: Add new item_type_id column as foreign key
    op.add_column('item_master',
        sa.Column('item_type_id', sa.Integer(), nullable=True)
    )
    
    # Step 2: Create foreign key constraint
    op.create_foreign_key(
        'fk_item_master_item_type_id',
        'item_master', 'item_type',
        ['item_type_id'], ['id']
    )
    
    # Step 3: Populate item_type_id based on existing item_type string values
    # Create a connection to execute raw SQL
    connection = op.get_bind()
    
    # Map string values to IDs (based on the current data)
    type_mappings = {
        'RM': 1,
        'WIP': 3, 
        'WIPF': 4,
        'FG': 5
    }
    
    # Update each record
    for type_name, type_id in type_mappings.items():
        connection.execute(
            sa.text("UPDATE item_master SET item_type_id = :type_id WHERE item_type = :type_name"),
            {'type_id': type_id, 'type_name': type_name}
        )
    
    # Step 4: Make item_type_id NOT NULL after populating
    op.alter_column('item_master', 'item_type_id', nullable=False)
    
    # Step 5: Drop the old item_type string column
    op.drop_column('item_master', 'item_type')

def downgrade():
    # Step 1: Add back the item_type string column
    op.add_column('item_master',
        sa.Column('item_type', sa.String(20), nullable=True)
    )
    
    # Step 2: Populate item_type string based on item_type_id
    connection = op.get_bind()
    
    # Reverse mapping (ID to string)
    id_mappings = {
        1: 'RM',
        3: 'WIP',
        4: 'WIPF', 
        5: 'FG'
    }
    
    # Update each record
    for type_id, type_name in id_mappings.items():
        connection.execute(
            sa.text("UPDATE item_master SET item_type = :type_name WHERE item_type_id = :type_id"),
            {'type_name': type_name, 'type_id': type_id}
        )
    
    # Step 3: Make item_type NOT NULL
    op.alter_column('item_master', 'item_type', nullable=False)
    
    # Step 4: Drop foreign key constraint
    op.drop_constraint('fk_item_master_item_type_id', 'item_master', type_='foreignkey')
    
    # Step 5: Drop item_type_id column
    op.drop_column('item_master', 'item_type_id') 