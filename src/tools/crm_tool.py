"""CRM Tool for interacting with CRM MCP server."""

import asyncio
from functools import wraps
from typing import Any, Callable, Dict, Optional

from src.mcp_servers.mock_crm_server import MockCRMServer
from src.utils.logger import LoggerMixin


def retry_on_error(max_retries: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """Decorator for retrying function calls on error.

    Args:
        max_retries: Maximum number of retry attempts
        delay: Initial delay between retries in seconds
        backoff: Backoff multiplier for delay
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_error = None
            current_delay = delay

            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if attempt < max_retries - 1:
                        await asyncio.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        raise

            raise last_error

        return wrapper

    return decorator


class CRMTool(LoggerMixin):
    """Tool for interacting with CRM MCP server with error handling and retry logic."""

    def __init__(
        self,
        crm_server: MockCRMServer,
        cache_enabled: bool = True,
        cache_ttl: int = 3600,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        retry_backoff: float = 2.0,
    ) -> None:
        """Initialize CRM tool.

        Args:
            crm_server: CRM MCP server instance
            cache_enabled: Whether to enable caching
            cache_ttl: Cache time-to-live in seconds
            max_retries: Maximum retry attempts
            retry_delay: Initial retry delay
            retry_backoff: Retry backoff multiplier
        """
        self.crm_server = crm_server
        self.cache_enabled = cache_enabled
        self.cache_ttl = cache_ttl
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.retry_backoff = retry_backoff
        self._cache: Dict[str, tuple[Any, float]] = {}
        self.logger.info("CRM tool initialized")

    def _get_cache_key(self, tool_name: str, parameters: Dict[str, Any]) -> str:
        """Generate cache key from tool name and parameters.

        Args:
            tool_name: Tool name
            parameters: Tool parameters

        Returns:
            Cache key string
        """
        import json

        params_str = json.dumps(parameters, sort_keys=True)
        return f"{tool_name}:{params_str}"

    def _is_cache_valid(self, cached_time: float) -> bool:
        """Check if cache entry is still valid.

        Args:
            cached_time: Cache timestamp

        Returns:
            True if cache is valid
        """
        import time

        if not self.cache_enabled:
            return False

        return (time.time() - cached_time) < self.cache_ttl

    @retry_on_error(max_retries=3, delay=1.0, backoff=2.0)
    async def get_lead_info(
        self,
        lead_id: Optional[str] = None,
        email: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get lead information.

        Args:
            lead_id: Lead ID
            email: Lead email

        Returns:
            Lead information dictionary

        Raises:
            ValueError: If neither lead_id nor email is provided
            RuntimeError: If CRM call fails after retries
        """
        if not lead_id and not email:
            raise ValueError("Either lead_id or email must be provided")

        # Check cache
        params = {"lead_id": lead_id, "email": email}
        cache_key = self._get_cache_key("get_lead_info", params)

        if self.cache_enabled and cache_key in self._cache:
            cached_data, cached_time = self._cache[cache_key]
            if self._is_cache_valid(cached_time):
                self.logger.debug("Cache hit", cache_key=cache_key)
                return cached_data

        try:
            result = await self.crm_server.call("get_lead_info", params)

            # Cache result
            if self.cache_enabled:
                import time

                self._cache[cache_key] = (result, time.time())

            return result
        except Exception as e:
            self.logger.error("Failed to get lead info", error=str(e), lead_id=lead_id, email=email)
            raise RuntimeError(f"Failed to get lead info: {str(e)}") from e

    @retry_on_error(max_retries=3, delay=1.0, backoff=2.0)
    async def update_lead_status(
        self,
        lead_id: str,
        status: str,
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Update lead status.

        Args:
            lead_id: Lead ID
            status: New status
            notes: Optional notes

        Returns:
            Update result dictionary

        Raises:
            RuntimeError: If CRM call fails after retries
        """
        try:
            result = await self.crm_server.call(
                "update_lead_status",
                {
                    "lead_id": lead_id,
                    "status": status,
                    "notes": notes,
                },
            )

            # Invalidate cache for this lead
            if self.cache_enabled:
                # Remove all cache entries for this lead
                keys_to_remove = [
                    key for key in self._cache.keys() if f'"lead_id": "{lead_id}"' in key
                ]
                for key in keys_to_remove:
                    del self._cache[key]

            return result
        except Exception as e:
            self.logger.error(
                "Failed to update lead status", error=str(e), lead_id=lead_id, status=status
            )
            raise RuntimeError(f"Failed to update lead status: {str(e)}") from e

    @retry_on_error(max_retries=3, delay=1.0, backoff=2.0)
    async def get_sales_history(
        self,
        lead_id: Optional[str] = None,
        limit: int = 10,
    ) -> Dict[str, Any]:
        """Get sales history.

        Args:
            lead_id: Optional lead ID filter
            limit: Maximum records to return

        Returns:
            Sales history dictionary

        Raises:
            RuntimeError: If CRM call fails after retries
        """
        # Check cache
        params = {"lead_id": lead_id, "limit": limit}
        cache_key = self._get_cache_key("get_sales_history", params)

        if self.cache_enabled and cache_key in self._cache:
            cached_data, cached_time = self._cache[cache_key]
            if self._is_cache_valid(cached_time):
                self.logger.debug("Cache hit", cache_key=cache_key)
                return cached_data

        try:
            result = await self.crm_server.call("get_sales_history", params)

            # Cache result
            if self.cache_enabled:
                import time

                self._cache[cache_key] = (result, time.time())

            return result
        except Exception as e:
            self.logger.error(
                "Failed to get sales history", error=str(e), lead_id=lead_id, limit=limit
            )
            raise RuntimeError(f"Failed to get sales history: {str(e)}") from e

    def clear_cache(self) -> None:
        """Clear the cache."""
        self._cache.clear()
        self.logger.debug("Cache cleared")

