"""
Rate limiting middleware using Redis.
"""

import time
from typing import Optional
from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import redis.asyncio as redis
import structlog

from core.config import settings

logger = structlog.get_logger(__name__)

# Redis connection for rate limiting
redis_client: Optional[redis.Redis] = None

def get_redis_client() -> redis.Redis:
    """Get Redis client for rate limiting."""
    global redis_client
    if redis_client is None:
        redis_client = redis.from_url(settings.redis_url, encoding="utf-8", decode_responses=True)
    return redis_client


def get_rate_limit_key(request: Request) -> str:
    """Generate rate limit key from request."""
    # Use IP address as default identifier
    ip = get_remote_address(request)
    
    # If user is authenticated, use user ID instead
    user_id = getattr(request.state, 'user_id', None)
    if user_id:
        return f"rate_limit:user:{user_id}"
    
    return f"rate_limit:ip:{ip}"


# Create limiter instance
limiter = Limiter(
    key_func=get_rate_limit_key,
    default_limits=[f"{settings.rate_limit_per_minute}/minute"]
)


class RateLimitMiddleware:
    """Rate limiting middleware."""
    
    def __init__(self, app, calls: int = 60, period: int = 60):
        self.app = app
        self.calls = calls
        self.period = period
        self.redis_client = get_redis_client()
    
    async def __call__(self, request: Request, call_next):
        """Process request with rate limiting."""
        # Skip rate limiting for health checks
        if request.url.path in ["/health", "/", "/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)
        
        # Generate rate limit key
        key = get_rate_limit_key(request)
        
        try:
            # Get current request count
            current = await self.redis_client.get(key)
            
            if current is None:
                # First request in the window
                await self.redis_client.setex(key, self.period, 1)
                request.state.rate_limit_remaining = self.calls - 1
            else:
                current = int(current)
                if current >= self.calls:
                    # Rate limit exceeded
                    logger.warning(
                        "Rate limit exceeded",
                        key=key,
                        current=current,
                        limit=self.calls,
                        path=request.url.path
                    )
                    
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail={
                            "error": "Rate limit exceeded",
                            "retry_after": self.period
                        }
                    )
                else:
                    # Increment counter
                    await self.redis_client.incr(key)
                    request.state.rate_limit_remaining = self.calls - current - 1
            
            # Process request
            response = await call_next(request)
            
            # Add rate limit headers
            response.headers["X-RateLimit-Limit"] = str(self.calls)
            response.headers["X-RateLimit-Remaining"] = str(getattr(request.state, 'rate_limit_remaining', 0))
            response.headers["X-RateLimit-Reset"] = str(int(time.time()) + self.period)
            
            return response
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Rate limiting error", error=str(e))
            # If rate limiting fails, allow the request
            return await call_next(request)


async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    """Handle rate limit exceeded errors."""
    logger.warning(
        "Rate limit exceeded",
        path=request.url.path,
        detail=str(exc.detail)
    )
    
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={
            "error": "Rate limit exceeded",
            "detail": str(exc.detail),
            "retry_after": 60
        }
    ) 