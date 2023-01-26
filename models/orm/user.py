"""
User domain SQLAlchemy models.
"""

from datetime import datetime
from typing import List, Optional
from sqlalchemy import String, Boolean, DateTime, ForeignKey, Text, Index, Table, Integer, Column
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid

from .base import Base, TimestampMixin


# Association table for many-to-many relationship between users and roles
user_roles = Table(
    'user_roles',
    Base.metadata,
    Column('user_id', UUID(as_uuid=True), ForeignKey('user.id'), primary_key=True),
    Column('role_id', UUID(as_uuid=True), ForeignKey('role.id'), primary_key=True)
)

# Association table for many-to-many relationship between roles and permissions
role_permissions = Table(
    'role_permissions',
    Base.metadata,
    Column('role_id', UUID(as_uuid=True), ForeignKey('role.id'), primary_key=True),
    Column('permission_id', UUID(as_uuid=True), ForeignKey('permission.id'), primary_key=True)
)


class Permission(Base, TimestampMixin):
    """Permission model for RBAC."""
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    codename: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    resource: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g., 'product', 'order', 'user'
    action: Mapped[str] = mapped_column(String(50), nullable=False)    # e.g., 'create', 'read', 'update', 'delete'
    
    # Relationships
    roles: Mapped[List["Role"]] = relationship(
        "Role",
        secondary=role_permissions,
        back_populates="permissions"
    )
    
    def __repr__(self) -> str:
        return f"<Permission(codename={self.codename}, resource={self.resource}, action={self.action})>"


class Role(Base, TimestampMixin):
    """Role model for RBAC."""
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Role hierarchy level (higher number = more privileges)
    level: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Relationships
    users: Mapped[List["User"]] = relationship(
        "User",
        secondary=user_roles,
        back_populates="roles"
    )
    permissions: Mapped[List["Permission"]] = relationship(
        "Permission",
        secondary=role_permissions,
        back_populates="roles"
    )
    
    def __repr__(self) -> str:
        return f"<Role(name={self.name}, level={self.level})>"


class User(Base, TimestampMixin):
    """User model supporting both registered and guest users."""
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    email: Mapped[Optional[str]] = mapped_column(String(255), unique=True, nullable=True)
    username: Mapped[Optional[str]] = mapped_column(String(50), unique=True, nullable=True)
    first_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    
    # Password hash (null for guest users)
    password_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # User type and status
    is_guest: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_staff: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Session ID for guest users
    session_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Last login tracking
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    roles: Mapped[List["Role"]] = relationship(
        "Role",
        secondary=user_roles,
        back_populates="users"
    )
    addresses: Mapped[List["Address"]] = relationship(
        "Address", 
        back_populates="user",
        cascade="all, delete-orphan"
    )
    cart: Mapped[Optional["Cart"]] = relationship(
        "Cart", 
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan"
    )
    orders: Mapped[List["Order"]] = relationship(
        "Order", 
        back_populates="user",
        cascade="all, delete-orphan"
    )
    reviews: Mapped[List["Review"]] = relationship(
        "Review", 
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    # Indexes for performance
    __table_args__ = (
        Index('ix_user_email', 'email'),
        Index('ix_user_session_id', 'session_id'),
        Index('ix_user_is_guest', 'is_guest'),
        Index('ix_user_is_staff', 'is_staff'),
    )
    
    def has_permission(self, permission_codename: str) -> bool:
        """Check if user has a specific permission."""
        if self.is_guest:
            return False
        
        for role in self.roles:
            if not role.is_active:
                continue
            for permission in role.permissions:
                if permission.codename == permission_codename:
                    return True
        return False
    
    def has_role(self, role_name: str) -> bool:
        """Check if user has a specific role."""
        return any(role.name == role_name and role.is_active for role in self.roles)
    
    def get_permissions(self) -> List[str]:
        """Get all permission codenames for this user."""
        permissions = set()
        for role in self.roles:
            if role.is_active:
                for permission in role.permissions:
                    permissions.add(permission.codename)
        return list(permissions)
    
    def is_admin(self) -> bool:
        """Check if user is an admin (has admin or super_admin role)."""
        return self.has_role('admin') or self.has_role('super_admin')
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, is_guest={self.is_guest})>"


class Address(Base, TimestampMixin):
    """User address model."""
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user.id"),
        nullable=False
    )
    
    # Address details
    label: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # e.g., "Home", "Work"
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    company: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    street_address_1: Mapped[str] = mapped_column(String(255), nullable=False)
    street_address_2: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    state: Mapped[str] = mapped_column(String(100), nullable=False)
    postal_code: Mapped[str] = mapped_column(String(20), nullable=False)
    country: Mapped[str] = mapped_column(String(2), nullable=False)  # ISO 3166-1 alpha-2
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    
    # Default address flag
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="addresses")
    
    def __repr__(self) -> str:
        return f"<Address(id={self.id}, user_id={self.user_id}, label={self.label})>" 