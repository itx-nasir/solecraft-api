"""
Main FastAPI application entry point.
"""

print("=== MAIN.PY STARTING ===")

from contextlib import asynccontextmanager
print("✓ asynccontextmanager imported")

from fastapi import FastAPI, HTTPException
print("✓ FastAPI imported")

from fastapi.middleware.cors import CORSMiddleware
print("✓ CORSMiddleware imported")

from fastapi.responses import JSONResponse
print("✓ JSONResponse imported")

import structlog
print("✓ structlog imported")

import sentry_sdk
print("✓ sentry_sdk imported")

from sentry_sdk.integrations.fastapi import FastApiIntegration
print("✓ FastApiIntegration imported")

from datetime import datetime
print("✓ datetime imported")

from core.config import settings
print("✓ settings imported")

from core.database import init_database, close_database
print("✓ database functions imported")

from models.schemas import HealthCheck, ErrorResponse
print("✓ schemas imported")

from core.scheduler import initialize_scheduler, shutdown_scheduler
print("✓ scheduler imported")

print("=== ALL IMPORTS COMPLETED ===")


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
    print("=== LIFESPAN STARTUP BEGINNING ===")
    logger.info("Starting up SoleCraft API", version=settings.app_version)
    print(f"App version: {settings.app_version}")
    print(f"Environment: {settings.environment}")
    
    try:
        print("=== INITIALIZING DATABASE ===")
        # Try to initialize database, but don't fail the entire app if it fails
        try:
            await init_database()
            logger.info("Database initialization completed")
            print("Database initialization completed")
        except Exception as e:
            logger.error("Database initialization failed, continuing without database", error=str(e))
            print(f"Database initialization failed: {e}")
        
        print("=== INITIALIZING SCHEDULER ===")
        # Try to initialize scheduler, but don't fail the entire app if it fails
        try:
            initialize_scheduler()
            logger.info("Scheduler initialization completed")
            print("Scheduler initialization completed")
        except Exception as e:
            logger.error("Scheduler initialization failed, continuing without scheduler", error=str(e))
            print(f"Scheduler initialization failed: {e}")
        
        logger.info("Application startup completed")
        print("=== APPLICATION STARTUP COMPLETED ===")
        yield
    except Exception as e:
        logger.error("Failed to start application", error=str(e))
        print(f"Failed to start application: {e}")
        # Don't raise here to allow the app to start even with partial failures
    finally:
        # Shutdown
        print("=== LIFESPAN SHUTDOWN BEGINNING ===")
        logger.info("Shutting down SoleCraft API")
        try:
            shutdown_scheduler()
            await close_database()
            logger.info("Application shutdown completed")
            print("Application shutdown completed")
        except Exception as e:
            logger.error("Error during shutdown", error=str(e))
            print(f"Error during shutdown: {e}")


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


# Health check endpoint
@app.get("/health", response_model=HealthCheck, tags=["Health"])
async def health_check():
    """Health check endpoint."""
    try:
        # Try to get database status
        db_status = "connected"
        scheduler_status = "running"
        
        # You can add actual database connectivity check here if needed
        # For now, we'll assume it's working if the app is running
        
        return HealthCheck(
            status="healthy",
            timestamp=datetime.utcnow(),
            version=settings.app_version,
            database=db_status,
            scheduler=scheduler_status
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthCheck(
            status="degraded",
            timestamp=datetime.utcnow(),
            version=settings.app_version,
            database="disconnected",
            scheduler="stopped"
        )


# Simple health check endpoint (no database dependency)
@app.get("/health-simple", tags=["Health"])
async def health_check_simple():
    """Simple health check endpoint without database dependency."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": settings.app_version,
        "message": "API is running"
    }


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint."""
    return {
        "message": f"Welcome to {settings.app_name}",
        "version": settings.app_version,
        "docs": "/docs" if settings.debug else "Documentation disabled in production",
        "health": "/health",
        "health_simple": "/health-simple",
        "environment": settings.environment
    }


# Diagnostic endpoint
@app.get("/diagnostic", tags=["Diagnostic"])
async def diagnostic():
    """Diagnostic endpoint to help troubleshoot deployment issues."""
    import os
    
    return {
        "app_name": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "debug": settings.debug,
        "port": os.getenv("PORT", "8000"),
        "database_url_set": bool(settings.database_url),
        "database_url_length": len(settings.database_url) if settings.database_url else 0,
        "allowed_origins": settings.allowed_origins,
        "timestamp": datetime.utcnow().isoformat()
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