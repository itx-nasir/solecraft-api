"""
Service layer for admin-related business logic.
"""
from typing import List, Tuple, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func

from models.orm.order import Order
from models.orm.user import User
from models.orm.product import Product
from models.schemas.order import OrderStatus, PaymentStatus, OrderUpdate


class AdminService:
    """Service for admin operations."""

    async def get_dashboard_statistics(self, session: AsyncSession) -> dict:
        """Get dashboard statistics."""
        total_users_result = await session.execute(select(func.count(User.id)))
        total_orders_result = await session.execute(select(func.count(Order.id)))
        total_products_result = await session.execute(select(func.count(Product.id)))

        return {
            "total_users": total_users_result.scalar_one(),
            "total_orders": total_orders_result.scalar_one(),
            "total_products": total_products_result.scalar_one(),
        }

    async def list_all_orders(self, session: AsyncSession) -> List[Order]:
        """List all orders for admin."""
        result = await session.execute(select(Order).order_by(Order.created_at.desc()))
        return list(result.scalars().all())

    async def update_order_status(
        self, session: AsyncSession, order_id: UUID, status_update: OrderUpdate
    ) -> Optional[Order]:
        """Update the status of an order."""
        order = await session.get(Order, order_id)
        if not order:
            return None
            
        update_data = status_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(order, key, value)
            
        await session.flush()
        await session.refresh(order)
        return order

admin_service = AdminService() 