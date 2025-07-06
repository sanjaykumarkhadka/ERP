"""create raw_materials table

Revision ID: create_raw_materials_table
Revises: rename_raw_material_table
Create Date: 2024-03-19 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'create_raw_materials_table'
down_revision = 'rename_raw_material_table'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('raw_materials',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('raw_material', sa.String(length=255), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('raw_material')
    )


def downgrade():
    op.drop_table('raw_materials') 