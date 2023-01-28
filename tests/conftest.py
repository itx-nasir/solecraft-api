"""
Pytest configuration and fixtures.
"""

import asyncio
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from main import app
from core.config import settings
from infrastructure.database import get_async_session
from models.orm import Base
from middleware.auth import get_password_hash, create_access_token

# Test database URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def test_db():
    """Create a test database."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
        echo=False,
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    TestSessionLocal = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    yield TestSessionLocal
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_db):
    """Create a database session for testing."""
    async with test_db() as session:
        yield session


@pytest_asyncio.fixture
async def client(db_session):
    """Create a test client."""
    def override_get_db():
        return db_session
    
    app.dependency_overrides[get_async_session] = override_get_db
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()


@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        "email": "test@example.com",
        "password": "TestPassword123!",
        "first_name": "Test",
        "last_name": "User",
        "username": "testuser"
    }


@pytest.fixture
def sample_guest_data():
    """Sample guest user data for testing."""
    return {
        "session_id": "test_session_123",
        "email": "guest@example.com"
    }


@pytest.fixture
def sample_address_data():
    """Sample address data for testing."""
    return {
        "street_address": "123 Test Street",
        "city": "Test City",
        "state": "Test State",
        "postal_code": "12345",
        "country": "Test Country",
        "address_type": "home",
        "is_default": True
    }


@pytest_asyncio.fixture
async def admin_user_token(client: AsyncClient, db_session: AsyncSession):
    """Create an admin user and return its auth token."""
    from models.orm import User, Role, Permission
    from middleware.auth import get_password_hash, create_access_token

    # Create necessary permissions
    product_create_perm = Permission(
        name="Create Product",
        codename="product:create",
        resource="product",
        action="create"
    )
    product_update_perm = Permission(
        name="Update Product", 
        codename="product:update",
        resource="product",
        action="update"
    )
    product_delete_perm = Permission(
        name="Delete Product",
        codename="product:delete", 
        resource="product",
        action="delete"
    )
    
    db_session.add_all([product_create_perm, product_update_perm, product_delete_perm])
    await db_session.flush()

    # Create admin role with permissions
    admin_role = Role(
        name="admin",
        description="Administrator role for testing",
        level=90,
        permissions=[product_create_perm, product_update_perm, product_delete_perm]
    )
    db_session.add(admin_role)
    await db_session.flush()

    admin_email = "admin@example.com"
    admin_password = "AdminPassword123!"
    
    # Create admin user directly in the database
    admin_user = User(
        email=admin_email,
        password_hash=get_password_hash(admin_password),
        is_staff=True,
        is_active=True,
        is_verified=True,
        first_name="Admin",
        last_name="User",
        roles=[admin_role]
    )
    db_session.add(admin_user)
    await db_session.commit()
    await db_session.refresh(admin_user)

    # Create an access token for the admin user
    access_token = create_access_token(data={"sub": str(admin_user.id)})
    return access_token


@pytest_asyncio.fixture
async def test_category(db_session: AsyncSession):
    """Create a test category."""
    from models.orm import Category
    from slugify import slugify
    
    name = "Test Category"
    category = Category(name=name, slug=slugify(name))
    db_session.add(category)
    await db_session.commit()
    await db_session.refresh(category)
    return category


@pytest.fixture
def sample_product_data(test_category):
    """Sample product data for testing."""
    return {
        "name": "Test Shoe",
        "slug": "test-shoe",
        "description": "A very fine shoe for testing.",
        "base_price": "99.99",
        "category_id": str(test_category.id),
        "is_active": True
    } 