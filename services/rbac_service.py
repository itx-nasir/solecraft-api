"""
RBAC (Role-Based Access Control) service.
"""

from typing import List, Optional, Dict, Any
from uuid import UUID
import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from models.orm import User, Role, Permission
from models.schemas import (
    RoleCreate, RoleUpdate, RoleResponse,
    PermissionCreate, PermissionUpdate, PermissionResponse,
    UserRoleAssignment, PaginationParams
)

logger = structlog.get_logger(__name__)


class RBACService:
    """RBAC service for managing roles and permissions."""

    def __init__(self, session: AsyncSession):
        self.session = session

    # Permission Management
    async def create_permission(self, permission_data: PermissionCreate) -> PermissionResponse:
        """Create a new permission."""
        permission = Permission(**permission_data.model_dump())
        self.session.add(permission)
        await self.session.commit()
        await self.session.refresh(permission)
        
        logger.info("Permission created", permission_id=permission.id, codename=permission.codename)
        return PermissionResponse.model_validate(permission)

    async def get_permission(self, permission_id: UUID) -> Optional[PermissionResponse]:
        """Get permission by ID."""
        stmt = select(Permission).where(Permission.id == permission_id)
        result = await self.session.execute(stmt)
        permission = result.scalar_one_or_none()
        
        if permission:
            return PermissionResponse.model_validate(permission)
        return None

    async def list_permissions(
        self, 
        pagination: PaginationParams,
        resource: Optional[str] = None
    ) -> tuple[List[PermissionResponse], int]:
        """List permissions with optional filtering."""
        base_stmt = select(Permission)
        count_stmt = select(func.count(Permission.id))
        
        if resource:
            base_stmt = base_stmt.where(Permission.resource == resource)
            count_stmt = count_stmt.where(Permission.resource == resource)
        
        # Get total count
        count_result = await self.session.execute(count_stmt)
        total = count_result.scalar() or 0
        
        # Apply pagination
        stmt = (
            base_stmt
            .offset(pagination.offset)
            .limit(pagination.page_size)
            .order_by(Permission.resource, Permission.action)
        )
        
        result = await self.session.execute(stmt)
        permissions = result.scalars().all()
        
        permission_responses = [PermissionResponse.model_validate(p) for p in permissions]
        return permission_responses, total

    # Role Management
    async def create_role(self, role_data: RoleCreate) -> RoleResponse:
        """Create a new role with permissions."""
        role_dict = role_data.model_dump(exclude={"permission_ids"})
        role = Role(**role_dict)
        
        # Add permissions if specified
        if role_data.permission_ids:
            stmt = select(Permission).where(Permission.id.in_(role_data.permission_ids))
            result = await self.session.execute(stmt)
            permissions = result.scalars().all()
            role.permissions = list(permissions)
        
        self.session.add(role)
        await self.session.commit()
        await self.session.refresh(role, attribute_names=["permissions"])
        
        logger.info("Role created", role_id=role.id, role_name=role.name)
        return RoleResponse.model_validate(role)

    async def get_role(self, role_id: UUID) -> Optional[RoleResponse]:
        """Get role by ID with permissions."""
        stmt = (
            select(Role)
            .options(selectinload(Role.permissions))
            .where(Role.id == role_id)
        )
        result = await self.session.execute(stmt)
        role = result.scalar_one_or_none()
        
        if role:
            return RoleResponse.model_validate(role)
        return None

    async def update_role(self, role_id: UUID, role_data: RoleUpdate) -> Optional[RoleResponse]:
        """Update a role."""
        stmt = (
            select(Role)
            .options(selectinload(Role.permissions))
            .where(Role.id == role_id)
        )
        result = await self.session.execute(stmt)
        role = result.scalar_one_or_none()
        
        if not role:
            return None
        
        # Update role fields
        update_data = role_data.model_dump(exclude_unset=True, exclude={"permission_ids"})
        for field, value in update_data.items():
            setattr(role, field, value)
        
        # Update permissions if specified
        if role_data.permission_ids is not None:
            stmt = select(Permission).where(Permission.id.in_(role_data.permission_ids))
            result = await self.session.execute(stmt)
            permissions = result.scalars().all()
            role.permissions = list(permissions)
        
        await self.session.commit()
        await self.session.refresh(role, attribute_names=["permissions"])
        
        logger.info("Role updated", role_id=role.id, role_name=role.name)
        return RoleResponse.model_validate(role)

    async def list_roles(self, pagination: PaginationParams) -> tuple[List[RoleResponse], int]:
        """List roles with permissions."""
        base_stmt = select(Role).options(selectinload(Role.permissions))
        count_stmt = select(func.count(Role.id))
        
        # Get total count
        count_result = await self.session.execute(count_stmt)
        total = count_result.scalar() or 0
        
        # Apply pagination
        stmt = (
            base_stmt
            .offset(pagination.offset)
            .limit(pagination.page_size)
            .order_by(Role.level.desc(), Role.name)
        )
        
        result = await self.session.execute(stmt)
        roles = result.scalars().all()
        
        role_responses = [RoleResponse.model_validate(r) for r in roles]
        return role_responses, total

    # User Role Assignment
    async def assign_roles_to_user(self, assignment: UserRoleAssignment) -> bool:
        """Assign roles to a user."""
        # Get user
        user_stmt = (
            select(User)
            .options(selectinload(User.roles))
            .where(User.id == assignment.user_id)
        )
        user_result = await self.session.execute(user_stmt)
        user = user_result.scalar_one_or_none()
        
        if not user:
            raise ValueError("User not found")
        
        # Get roles
        roles_stmt = select(Role).where(Role.id.in_(assignment.role_ids))
        roles_result = await self.session.execute(roles_stmt)
        roles = roles_result.scalars().all()
        
        # Assign roles
        user.roles = list(roles)
        user.is_staff = len(roles) > 0  # Set is_staff if user has any roles
        
        await self.session.commit()
        
        logger.info(
            "Roles assigned to user", 
            user_id=user.id, 
            role_count=len(roles),
            role_names=[r.name for r in roles]
        )
        return True

    async def remove_role_from_user(self, user_id: UUID, role_id: UUID) -> bool:
        """Remove a specific role from a user."""
        user_stmt = (
            select(User)
            .options(selectinload(User.roles))
            .where(User.id == user_id)
        )
        user_result = await self.session.execute(user_stmt)
        user = user_result.scalar_one_or_none()
        
        if not user:
            return False
        
        # Remove the role
        user.roles = [role for role in user.roles if role.id != role_id]
        user.is_staff = len(user.roles) > 0
        
        await self.session.commit()
        
        logger.info("Role removed from user", user_id=user.id, role_id=role_id)
        return True

    async def get_user_permissions(self, user_id: UUID) -> List[str]:
        """Get all permission codenames for a user."""
        stmt = (
            select(User)
            .options(selectinload(User.roles).selectinload(Role.permissions))
            .where(User.id == user_id)
        )
        result = await self.session.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            return []
        
        return user.get_permissions()

    # Predefined Role Creation
    async def create_default_roles_and_permissions(self):
        """Create default roles and permissions for the system."""
        # Define permissions
        permissions_data = [
            # Product permissions
            {"name": "Create Product", "codename": "product:create", "resource": "product", "action": "create"},
            {"name": "Read Product", "codename": "product:read", "resource": "product", "action": "read"},
            {"name": "Update Product", "codename": "product:update", "resource": "product", "action": "update"},
            {"name": "Delete Product", "codename": "product:delete", "resource": "product", "action": "delete"},
            
            # Category permissions
            {"name": "Create Category", "codename": "category:create", "resource": "category", "action": "create"},
            {"name": "Update Category", "codename": "category:update", "resource": "category", "action": "update"},
            {"name": "Delete Category", "codename": "category:delete", "resource": "category", "action": "delete"},
            
            # Order permissions
            {"name": "Read Order", "codename": "order:read", "resource": "order", "action": "read"},
            {"name": "Update Order", "codename": "order:update", "resource": "order", "action": "update"},
            {"name": "Process Order", "codename": "order:process", "resource": "order", "action": "process"},
            {"name": "Cancel Order", "codename": "order:cancel", "resource": "order", "action": "cancel"},
            
            # User permissions
            {"name": "Read User", "codename": "user:read", "resource": "user", "action": "read"},
            {"name": "Update User", "codename": "user:update", "resource": "user", "action": "update"},
            {"name": "Delete User", "codename": "user:delete", "resource": "user", "action": "delete"},
            
            # Review permissions
            {"name": "Moderate Review", "codename": "review:moderate", "resource": "review", "action": "moderate"},
            {"name": "Delete Review", "codename": "review:delete", "resource": "review", "action": "delete"},
            
            # Discount permissions
            {"name": "Create Discount", "codename": "discount:create", "resource": "discount", "action": "create"},
            {"name": "Update Discount", "codename": "discount:update", "resource": "discount", "action": "update"},
            {"name": "Delete Discount", "codename": "discount:delete", "resource": "discount", "action": "delete"},
            
            # System permissions
            {"name": "Manage Roles", "codename": "role:manage", "resource": "role", "action": "manage"},
            {"name": "Manage Permissions", "codename": "permission:manage", "resource": "permission", "action": "manage"},
            {"name": "System Admin", "codename": "system:admin", "resource": "system", "action": "admin"},
        ]
        
        # Create permissions
        permission_map = {}
        for perm_data in permissions_data:
            # Check if permission already exists
            stmt = select(Permission).where(Permission.codename == perm_data["codename"])
            result = await self.session.execute(stmt)
            existing = result.scalar_one_or_none()
            
            if not existing:
                permission = Permission(**perm_data)
                self.session.add(permission)
                await self.session.flush()
                permission_map[perm_data["codename"]] = permission
            else:
                permission_map[perm_data["codename"]] = existing
        
        # Define roles with their permissions
        roles_data = [
            {
                "name": "customer",
                "description": "Regular customer with basic access",
                "level": 1,
                "permissions": []  # Customers don't need special permissions
            },
            {
                "name": "customer_service",
                "description": "Customer service representative",
                "level": 10,
                "permissions": ["order:read", "order:update", "user:read", "review:moderate"]
            },
            {
                "name": "inventory_manager",
                "description": "Manages products and inventory",
                "level": 20,
                "permissions": [
                    "product:create", "product:read", "product:update", "product:delete",
                    "category:create", "category:update", "category:delete"
                ]
            },
            {
                "name": "marketing_manager",
                "description": "Manages marketing and promotions",
                "level": 20,
                "permissions": [
                    "product:read", "product:update",
                    "discount:create", "discount:update", "discount:delete",
                    "review:moderate"
                ]
            },
            {
                "name": "order_fulfillment",
                "description": "Processes and fulfills orders",
                "level": 15,
                "permissions": ["order:read", "order:update", "order:process"]
            },
            {
                "name": "admin",
                "description": "System administrator",
                "level": 90,
                "permissions": [
                    "product:create", "product:read", "product:update", "product:delete",
                    "category:create", "category:update", "category:delete",
                    "order:read", "order:update", "order:process", "order:cancel",
                    "user:read", "user:update", "user:delete",
                    "review:moderate", "review:delete",
                    "discount:create", "discount:update", "discount:delete",
                    "role:manage"
                ]
            },
            {
                "name": "super_admin",
                "description": "Super administrator with full access",
                "level": 100,
                "permissions": list(permission_map.keys())  # All permissions
            }
        ]
        
        # Create roles
        for role_data in roles_data:
            # Check if role already exists
            stmt = select(Role).where(Role.name == role_data["name"])
            result = await self.session.execute(stmt)
            existing_role = result.scalar_one_or_none()
            
            if not existing_role:
                role = Role(
                    name=role_data["name"],
                    description=role_data["description"],
                    level=role_data["level"]
                )
                
                # Add permissions
                role_permissions = [
                    permission_map[perm_code] 
                    for perm_code in role_data["permissions"] 
                    if perm_code in permission_map
                ]
                role.permissions = role_permissions
                
                self.session.add(role)
        
        await self.session.commit()
        logger.info("Default roles and permissions created") 