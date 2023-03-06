"""
Remove categories and related product foreign key

Revision ID: remove_categories_20250714
Revises: ccf9a750c729
Create Date: 2025-07-14 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'remove_categories_20250714'
down_revision = 'ccf9a750c729'
branch_labels = None
depends_on = None

def upgrade():
    # Drop foreign key and column from product table
    with op.batch_alter_table('product') as batch_op:
        batch_op.drop_constraint('fk_product_category_id_category', type_='foreignkey')
        batch_op.drop_column('category_id')
        # batch_op.drop_index('ix_product_category_id')  # <-- Remove or comment out this line
    # Drop category table
    op.drop_table('category')

def downgrade():
    # Recreate category table
    op.create_table(
        'category',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('slug', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('image_url', sa.String(length=500), nullable=True),
        sa.Column('parent_id', sa.UUID(), nullable=True),
        sa.Column('meta_title', sa.String(length=200), nullable=True),
        sa.Column('meta_description', sa.String(length=500), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('sort_order', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['parent_id'], ['category.id'], name=op.f('fk_category_parent_id_category')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_category')),
        sa.UniqueConstraint('slug', name=op.f('uq_category_slug')),
    )
    # Re-add category_id to product table
    with op.batch_alter_table('product') as batch_op:
        batch_op.add_column(sa.Column('category_id', sa.UUID(), nullable=True))
        batch_op.create_foreign_key('fk_product_category_id_category', 'category', ['category_id'], ['id'])
        batch_op.create_index('ix_product_category_id', ['category_id']) 