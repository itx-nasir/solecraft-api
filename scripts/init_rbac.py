#!/usr/bin/env python3
"""
Initialize RBAC system with default roles and permissions.
Run this script to set up the initial roles and permissions in your database.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from core.config import settings
from services.rbac_service import RBACService
from models.orm import Base


async def init_rbac():
    """Initialize RBAC system with default roles and permissions."""
    print("🚀 Initializing RBAC system...")
    
    # Create database engine
    engine = create_async_engine(settings.database_url, echo=False)
    
    # Create tables if they don't exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create session
    SessionLocal = async_sessionmaker(engine, expire_on_commit=False)
    
    async with SessionLocal() as session:
        rbac_service = RBACService(session)
        
        try:
            await rbac_service.create_default_roles_and_permissions()
            print("✅ Successfully created default roles and permissions!")
            
            # List created roles
            from models.schemas import PaginationParams
            roles, total = await rbac_service.list_roles(PaginationParams(page=1, page_size=100))
            
            print(f"\n📋 Created {total} roles:")
            for role in roles:
                permissions_count = len(role.permissions)
                print(f"  • {role.name} (Level {role.level}) - {permissions_count} permissions")
            
            # List created permissions
            permissions, total = await rbac_service.list_permissions(PaginationParams(page=1, page_size=100))
            print(f"\n🔑 Created {total} permissions:")
            
            # Group permissions by resource
            by_resource = {}
            for perm in permissions:
                if perm.resource not in by_resource:
                    by_resource[perm.resource] = []
                by_resource[perm.resource].append(perm.action)
            
            for resource, actions in by_resource.items():
                print(f"  • {resource}: {', '.join(actions)}")
            
        except Exception as e:
            print(f"❌ Error initializing RBAC: {e}")
            raise
    
    await engine.dispose()
    print("\n🎉 RBAC initialization completed!")


async def create_admin_user():
    """Create a default admin user."""
    print("\n👤 Creating default admin user...")
    
    engine = create_async_engine(settings.database_url, echo=False)
    SessionLocal = async_sessionmaker(engine, expire_on_commit=False)
    
    async with SessionLocal() as session:
        from models.orm import User, Role
        from middleware.auth import get_password_hash
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload
        
        # Check if admin user already exists
        stmt = select(User).where(User.email == "admin@solecraft.com")
        result = await session.execute(stmt)
        existing_admin = result.scalar_one_or_none()
        
        if existing_admin:
            print("⚠️  Admin user already exists!")
            return
        
        # Get super_admin role
        stmt = select(Role).where(Role.name == "super_admin")
        result = await session.execute(stmt)
        super_admin_role = result.scalar_one_or_none()
        
        if not super_admin_role:
            print("❌ Super admin role not found! Run RBAC initialization first.")
            return
        
        # Create admin user
        admin_user = User(
            email="admin@solecraft.com",
            username="admin",
            first_name="System",
            last_name="Administrator",
            password_hash=get_password_hash("admin123!"),
            is_staff=True,
            is_active=True,
            is_verified=True
        )
        
        # Assign super_admin role
        admin_user.roles = [super_admin_role]
        
        session.add(admin_user)
        await session.commit()
        
        print("✅ Created admin user:")
        print("   Email: admin@solecraft.com")
        print("   Password: admin123!")
        print("   Role: super_admin")
        print("⚠️  IMPORTANT: Change the default password after first login!")
    
    await engine.dispose()


async def create_product_manager_user():
    """Create a default product manager user."""
    print("\n👤 Creating default product manager user...")

    engine = create_async_engine(settings.database_url, echo=False)
    SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

    async with SessionLocal() as session:
        from models.orm import User, Role
        from middleware.auth import get_password_hash
        from sqlalchemy import select
        
        # Check if product manager user already exists
        stmt = select(User).where(User.email == "manager@solecraft.com")
        result = await session.execute(stmt)
        existing_manager = result.scalar_one_or_none()

        if existing_manager:
            print("⚠️  Product manager user already exists!")
            return

        # Get inventory_manager role
        stmt = select(Role).where(Role.name == "inventory_manager")
        result = await session.execute(stmt)
        inventory_manager_role = result.scalar_one_or_none()

        if not inventory_manager_role:
            print("❌ Inventory manager role not found! Run RBAC initialization first.")
            return

        # Create product manager user
        manager_user = User(
            email="manager@solecraft.com",
            username="product_manager",
            first_name="Product",
            last_name="Manager",
            password_hash=get_password_hash("manager123!"),
            is_staff=True,
            is_active=True,
            is_verified=True
        )

        # Assign inventory_manager role
        manager_user.roles = [inventory_manager_role]

        session.add(manager_user)
        await session.commit()

        print("✅ Created product manager user:")
        print("   Email: manager@solecraft.com")
        print("   Password: manager123!")
        print("   Role: inventory_manager")

    await engine.dispose()


if __name__ == "__main__":
    print("🔐 SoleCraft RBAC Initialization")
    print("=" * 50)
    
    try:
        # Initialize RBAC
        asyncio.run(init_rbac())
        
        # Create admin user
        asyncio.run(create_admin_user())
        
        # Create product manager user
        asyncio.run(create_product_manager_user())
        
        print("\n" + "=" * 50)
        print("🎯 Next steps:")
        print("1. Login with admin@solecraft.com / admin123!")
        print("2. Change the default admin password")
        print("3. Create additional users and assign appropriate roles")
        print("4. Test the permission system")
        print("5. Use manager@solecraft.com to manage products")
        
    except KeyboardInterrupt:
        print("\n⏹️  Initialization cancelled by user")
    except Exception as e:
        print(f"\n💥 Fatal error: {e}")
        sys.exit(1)