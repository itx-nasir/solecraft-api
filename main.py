"""
Main FastAPI application entry point.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import structlog
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from datetime import datetime

from core.config import settings
from core.database import init_database, close_database
from models.schemas import HealthCheck, ErrorResponse
from core.scheduler import initialize_scheduler, shutdown_scheduler


# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)


# Initialize Sentry for error tracking
if settings.sentry_dsn:
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        integrations=[FastApiIntegration(auto_enabling=True)],
        traces_sample_rate=1.0 if settings.debug else 0.1,
        environment=settings.environment,
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager."""
    # Startup
    logger.info("Starting up SoleCraft API", version=settings.app_version)
    try:
        # Try to initialize database, but don't fail the entire app if it fails
        try:
            await init_database()
            logger.info("Database initialization completed")
        except Exception as e:
            logger.error("Database initialization failed, continuing without database", error=str(e))
        
        # Try to initialize scheduler, but don't fail the entire app if it fails
        try:
            initialize_scheduler()
            logger.info("Scheduler initialization completed")
        except Exception as e:
            logger.error("Scheduler initialization failed, continuing without scheduler", error=str(e))
        
        logger.info("Application startup completed")
        yield
    except Exception as e:
        logger.error("Failed to start application", error=str(e))
        # Don't raise here to allow the app to start even with partial failures
    finally:
        # Shutdown
        logger.info("Shutting down SoleCraft API")
        try:
            shutdown_scheduler()
            await close_database()
            logger.info("Application shutdown completed")
        except Exception as e:
            logger.error("Error during shutdown", error=str(e))


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Production-ready backend API for customizable shoes selling platform",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    openapi_url="/openapi.json" if settings.debug else None,
    lifespan=lifespan
)

# Import and include API routers
from api.auth import router as auth_router
from api.users import router as users_router
from api.products import router as products_router
from api.categories import router as categories_router
from api.cart import router as cart_router
from api.discounts import router as discounts_router
from api.orders import router as orders_router
from api.reviews import router as reviews_router
from api.search import router as search_router
from api.admin import router as admin_router

app.include_router(auth_router)
app.include_router(users_router)
app.include_router(products_router)
app.include_router(categories_router)
app.include_router(cart_router)
app.include_router(discounts_router)
app.include_router(orders_router)
app.include_router(reviews_router)
app.include_router(search_router)
app.include_router(admin_router)


# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handler
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc: HTTPException):
    """Handle HTTP exceptions."""
    logger.warning(
        "HTTP exception occurred",
        status_code=exc.status_code,
        detail=exc.detail,
        path=request.url.path
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            message=exc.detail,
            error_code=f"HTTP_{exc.status_code}"
        ).model_dump()
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc: Exception):
    """Handle general exceptions."""
    logger.error(
        "Unhandled exception occurred",
        error=str(exc),
        path=request.url.path,
        exc_info=True
    )
    
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            message="Internal server error",
            error_code="INTERNAL_ERROR"
        ).model_dump()
    )


# Comprehensive health check endpoint
@app.get("/health", response_model=HealthCheck, tags=["Health"])
async def health_check():
    """Comprehensive health check endpoint that verifies all system components."""
    import os
    from sqlalchemy import text
    
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "version": settings.app_version,
        "database": "disconnected",
        "scheduler": "stopped",
        "environment": settings.environment,
        "port": os.getenv("PORT", "8000")
    }
    
    # Check database connectivity
    try:
        from core.database import db_manager
        if db_manager._async_engine:
            async with db_manager._async_engine.begin() as conn:
                await conn.execute(text("SELECT 1"))
            health_status["database"] = "connected"
        else:
            health_status["database"] = "not_initialized"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        health_status["database"] = "error"
        health_status["status"] = "degraded"
    
    # Check scheduler status
    try:
        from core.scheduler import scheduler
        if scheduler.running:
            health_status["scheduler"] = "running"
        else:
            health_status["scheduler"] = "stopped"
            health_status["status"] = "degraded"
    except Exception as e:
        logger.error(f"Scheduler health check failed: {e}")
        health_status["scheduler"] = "error"
        health_status["status"] = "degraded"
    
    # Check environment variables
    required_env_vars = ["DATABASE_URL", "SECRET_KEY", "JWT_SECRET_KEY"]
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    if missing_vars:
        health_status["missing_env_vars"] = missing_vars
        health_status["status"] = "degraded"
    
    return HealthCheck(**health_status)


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint."""
    return {
        "message": f"Welcome to {settings.app_name}",
        "version": settings.app_version,
        "docs": "/docs" if settings.debug else "Documentation disabled in production",
        "health": "/health",
        "environment": settings.environment
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="info",
        access_log=True,
    ) 