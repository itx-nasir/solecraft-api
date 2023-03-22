"""
Seed initial admin and normal user, products, and orders

Revision ID: seeddata0100
Revises: c063fa819963
Create Date: 2025-07-15 01:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column
from sqlalchemy.dialects import postgresql
import uuid
from datetime import datetime
from passlib.context import CryptContext

# revision identifiers, used by Alembic.
revision = 'seeddata0100'
down_revision = 'c063fa819963'
branch_labels = None
depends_on = None

# Password hashing context (bcrypt)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def upgrade():
    conn = op.get_bind()
    now = datetime.utcnow()

    # Users
    admin_id = str(uuid.uuid4())
    user_id = str(uuid.uuid4())
    admin_email = 'admin@solecraft.com'
    user_email = 'user@solecraft.com'
    admin_password = get_password_hash('AdminPass123!')
    user_password = get_password_hash('UserPass123!')

    conn.execute(sa.text(f"""
        INSERT INTO "user" (id, email, username, first_name, last_name, phone, password_hash, is_guest, is_active, is_verified, is_admin, created_at, updated_at)
        VALUES
        ('{admin_id}', '{admin_email}', 'admin', 'Admin', 'User', '+10000000000', '{admin_password}', false, true, true, true, '{now}', '{now}'),
        ('{user_id}', '{user_email}', 'user', 'Normal', 'User', '+10000000001', '{user_password}', false, true, true, false, '{now}', '{now}')
    """))

    # Products
    product1_id = str(uuid.uuid4())
    product2_id = str(uuid.uuid4())
    conn.execute(sa.text(f"""
        INSERT INTO product (id, name, slug, description, short_description, base_price, is_active, is_featured, is_customizable, meta_title, meta_description, specifications, images, created_at, updated_at)
        VALUES
        ('{product1_id}', 'Classic White Sneaker', 'classic-white-sneaker', 'A timeless white sneaker for all occasions.', 'Timeless white sneaker', 79.99, true, true, false, 'Classic White Sneaker', 'A classic white sneaker for everyday wear.', '{{}}', '["/static/images/classic-white.jpg"]', '{now}', '{now}'),
        ('{product2_id}', 'Black Running Shoe', 'black-running-shoe', 'Lightweight running shoe for daily training.', 'Lightweight black running shoe', 99.99, true, false, false, 'Black Running Shoe', 'A lightweight black running shoe for runners.', '{{}}', '["/static/images/black-running.jpg"]', '{now}', '{now}')
    """))

    # Orders (one for each user)
    order1_id = str(uuid.uuid4())
    order2_id = str(uuid.uuid4())
    order1_number = 'ORD-1001'
    order2_number = 'ORD-1002'
    shipping_address = '{"first_name": "Admin", "last_name": "User", "street_address_1": "123 Admin St", "city": "Admin City", "state": "Admin State", "postal_code": "12345", "country": "US"}'
    billing_address = '{"first_name": "Admin", "last_name": "User", "street_address_1": "123 Admin St", "city": "Admin City", "state": "Admin State", "postal_code": "12345", "country": "US"}'
    conn.execute(sa.text(f"""
        INSERT INTO "order" (id, user_id, order_number, status, subtotal, tax_amount, shipping_amount, discount_amount, total_amount, shipping_address, billing_address, payment_status, created_at, updated_at)
        VALUES
        ('{order1_id}', '{admin_id}', '{order1_number}', 'confirmed', 79.99, 0.00, 0.00, 0.00, 79.99, '{shipping_address}', '{billing_address}', 'completed', '{now}', '{now}'),
        ('{order2_id}', '{user_id}', '{order2_number}', 'pending', 99.99, 0.00, 0.00, 0.00, 99.99, '{shipping_address}', '{billing_address}', 'pending', '{now}', '{now}')
    """))

    # Order Items
    orderitem1_id = str(uuid.uuid4())
    orderitem2_id = str(uuid.uuid4())
    conn.execute(sa.text(f"""
        INSERT INTO orderitem (id, order_id, product_id, product_name, variant_name, sku, quantity, unit_price, total_price, created_at, updated_at)
        VALUES
        ('{orderitem1_id}', '{order1_id}', '{product1_id}', 'Classic White Sneaker', '', 'SKU-CLASSIC-WHITE', 1, 79.99, 79.99, '{now}', '{now}'),
        ('{orderitem2_id}', '{order2_id}', '{product2_id}', 'Black Running Shoe', '', 'SKU-BLACK-RUN', 1, 99.99, 99.99, '{now}', '{now}')
    """))

def downgrade():
    conn = op.get_bind()
    conn.execute(sa.text("DELETE FROM orderitem"))
    conn.execute(sa.text("DELETE FROM \"order\""))
    conn.execute(sa.text("DELETE FROM product"))
    conn.execute(sa.text("DELETE FROM \"user\" WHERE email IN ('admin@solecraft.com', 'user@solecraft.com')")) 