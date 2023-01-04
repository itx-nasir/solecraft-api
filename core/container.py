"""
Dependency injection container using the Factory pattern.
"""

from typing import Type, Dict, Any, Callable
from functools import lru_cache
from sqlalchemy.ext.asyncio import AsyncSession

from repositories.user_repository import UserRepository, AddressRepository
from interfaces.repositories import IUserRepository


class Container:
    """Dependency injection container."""
    
    def __init__(self):
        self._services: Dict[str, Any] = {}
        self._factories: Dict[str, Callable] = {}
        self._register_factories()
    
    def _register_factories(self):
        """Register service factories."""
        # Repository factories
        self._factories['user_repository'] = lambda session: UserRepository(session)
        self._factories['address_repository'] = lambda session: AddressRepository(session)
    
    def get_repository(self, repository_type: str, session: AsyncSession) -> Any:
        """Get repository instance."""
        if repository_type not in self._factories:
            raise ValueError(f"Unknown repository type: {repository_type}")
        
        return self._factories[repository_type](session)
    
    def register_service(self, name: str, service: Any):
        """Register a service instance."""
        self._services[name] = service
    
    def get_service(self, name: str) -> Any:
        """Get service instance."""
        if name not in self._services:
            raise ValueError(f"Service not registered: {name}")
        return self._services[name]


@lru_cache()
def get_container() -> Container:
    """Get container instance."""
    return Container()


# Global container instance
container = get_container() 