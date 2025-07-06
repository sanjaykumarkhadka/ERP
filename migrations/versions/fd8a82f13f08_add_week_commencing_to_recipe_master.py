"""Add week_commencing to recipe_master

Revision ID: fd8a82f13f08
Revises: 
Create Date: 2025-06-06 10:12:29.515703

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fd8a82f13f08'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('recipe_master', sa.Column('week_commencing', sa.Date(), nullable=True))
    # Make existing rows have a default date (you may want to adjust this)
    op.execute("UPDATE recipe_master SET week_commencing = CURDATE() WHERE week_commencing IS NULL")
    # Then make it not nullable
    op.alter_column('recipe_master', 'week_commencing',
               existing_type=sa.Date(),
               nullable=False)


def downgrade():
    op.drop_column('recipe_master', 'week_commencing')
