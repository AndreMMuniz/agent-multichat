"""
Async-safe wrappers for database operations.
Prevents blocking the FastAPI event loop during graph execution.
"""

import asyncio
from functools import wraps
from typing import Callable, Any

def run_in_thread(func: Callable) -> Callable:
    """
    Decorator to run synchronous functions in a thread pool.
    Prevents blocking the async event loop.
    
    Usage:
        @run_in_thread
        def sync_db_operation(state):
            db = SessionLocal()
            # ... blocking operations ...
            db.close()
    """
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        # Run the synchronous function in a thread pool
        return await asyncio.to_thread(func, *args, **kwargs)
    
    return async_wrapper

# Alternative: Context manager for async database sessions
# This would be the "long-term" solution mentioned in the issue
class AsyncDatabaseSession:
    """
    Placeholder for future async database implementation.
    Would use sqlalchemy.ext.asyncio.AsyncSession
    """
    pass
