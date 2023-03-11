"""
Search API routes.
"""
from fastapi import APIRouter, Depends, status, Request, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from core.database import get_async_session
from services.search_service import search_service
from models.schemas.product import ProductSearchRequest, ProductListResponse
from models.schemas.common import PaginatedResponse, PaginationParams

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/search", tags=["Search"])

@router.get(
    "/products",
    response_model=PaginatedResponse[ProductListResponse],
    summary="Search for products",
    description="Search and filter products based on various criteria.",
)
async def search_products(
    request: Request,
    search_params: ProductSearchRequest = Depends(),
    pagination: PaginationParams = Depends(),
    session: AsyncSession = Depends(get_async_session),
):
    """Search for products."""
    try:
        products, total = await search_service.search_products(
            session, search_params, pagination
        )
        total_pages = (total + pagination.page_size - 1) // pagination.page_size
        return PaginatedResponse(
            items=products,
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
            total_pages=total_pages,
            has_next=pagination.page < total_pages,
            has_prev=pagination.page > 1,
        )
    except Exception as e:
        logger.error("Failed to search products", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search for products.",
        ) 