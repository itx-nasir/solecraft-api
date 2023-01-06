"""
Database infrastructure setup with SQLAlchemy async support.
"""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
import structlog

from core.config import settings
from models.orm import Base

logger = structlog.get_logger(__name__)


class DatabaseManager:
    """Database manager singleton for async SQLAlchemy operations."""
    
    _instance = None
    _async_engine = None
    _sync_engine = None
    _async_session_factory = None
    _sync_session_factory = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def initialize(self):
        """Initialize database engines and session factories."""
        # Async engine for application use
        self._async_engine = create_async_engine(
            settings.database_url,
            echo=settings.debug,
            pool_size=20,
            max_overflow=30,
            pool_pre_ping=True,
            pool_recycle=3600,  # 1 hour
        )
        
        # Sync engine for Alembic migrations
        self._sync_engine = create_engine(
            settings.database_url_sync,
            echo=settings.debug,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,
            pool_recycle=3600,
        )
        
        # Session factories
        self._async_session_factory = async_sessionmaker(
            bind=self._async_engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )
        
        self._sync_session_factory = sessionmaker(
            bind=self._sync_engine,
            autoflush=False,
        )
        
        logger.info("Database engines and session factories initialized")
    
    async def create_tables(self):
        """Create all database tables."""
        async with self._async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created")
    
    async def drop_tables(self):
        """Drop all database tables."""
        async with self._async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        logger.info("Database tables dropped")
    
    async def close(self):
        """Close database connections."""
        if self._async_engine:
            await self._async_engine.dispose()
        if self._sync_engine:
            self._sync_engine.dispose()
        logger.info("Database connections closed")
    
    def get_async_session(self) -> AsyncSession:
        """Get async database session."""
        if not self._async_session_factory:
            raise RuntimeError("Database not initialized")
        return self._async_session_factory()
    
    def get_sync_session(self):
        """Get sync database session."""
        if not self._sync_session_factory:
            raise RuntimeError("Database not initialized")
        return self._sync_session_factory()
    
    @property
    def async_engine(self):
        """Get async engine."""
        return self._async_engine
    
    @property
    def sync_engine(self):
        """Get sync engine."""
        return self._sync_engine


# Global database manager instance
db_manager = DatabaseManager()


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency function to get async database session.
    Used for FastAPI dependency injection.
    """
    session = db_manager.get_async_session()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


def get_sync_session():
    """
    Get sync database session.
    Used for Alembic migrations and synchronous operations.
    """
    return db_manager.get_sync_session()


async def init_database():
    """Initialize database on application startup."""
    try:
        db_manager.initialize()
        logger.info("Database initialization completed")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise


async def close_database():
    """Close database connections on application shutdown."""
    try:
        await db_manager.close()
        logger.info("Database connections closed successfully")
    except Exception as e:
        logger.error(f"Error closing database connections: {e}")
        raise 