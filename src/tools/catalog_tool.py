"""Catalog Tool for interacting with Catalog MCP server."""

import asyncio
from functools import wraps
from typing import Any, Callable, Dict, List, Optional

from src.mcp_servers.mock_catalog_server import MockCatalogServer
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


class CatalogTool(LoggerMixin):
    """Tool for interacting with Catalog MCP server with error handling and retry logic."""

    def __init__(
        self,
        catalog_server: MockCatalogServer,
        cache_enabled: bool = True,
        cache_ttl: int = 3600,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        retry_backoff: float = 2.0,
    ) -> None:
        """Initialize catalog tool.

        Args:
            catalog_server: Catalog MCP server instance
            cache_enabled: Whether to enable caching
            cache_ttl: Cache time-to-live in seconds
            max_retries: Maximum retry attempts
            retry_delay: Initial retry delay
            retry_backoff: Retry backoff multiplier
        """
        self.catalog_server = catalog_server
        self.cache_enabled = cache_enabled
        self.cache_ttl = cache_ttl
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.retry_backoff = retry_backoff
        self._cache: Dict[str, tuple[Any, float]] = {}
        self.logger.info("Catalog tool initialized")

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
    async def get_products(
        self,
        category: Optional[str] = None,
        target_audience: Optional[str] = None,
        limit: int = 100,
    ) -> Dict[str, Any]:
        """Get list of products.

        Args:
            category: Optional category filter
            target_audience: Optional target audience filter
            limit: Maximum number of products to return

        Returns:
            Products list dictionary

        Raises:
            RuntimeError: If catalog call fails after retries
        """
        # Check cache
        params = {"category": category, "target_audience": target_audience, "limit": limit}
        cache_key = self._get_cache_key("get_products", params)

        if self.cache_enabled and cache_key in self._cache:
            cached_data, cached_time = self._cache[cache_key]
            if self._is_cache_valid(cached_time):
                self.logger.debug("Cache hit", cache_key=cache_key)
                return cached_data

        try:
            result = await self.catalog_server.call("get_products", params)

            # Cache result
            if self.cache_enabled:
                import time

                self._cache[cache_key] = (result, time.time())

            return result
        except Exception as e:
            self.logger.error(
                "Failed to get products",
                error=str(e),
                category=category,
                target_audience=target_audience,
            )
            raise RuntimeError(f"Failed to get products: {str(e)}") from e

    @retry_on_error(max_retries=3, delay=1.0, backoff=2.0)
    async def get_product_details(self, product_id: str) -> Dict[str, Any]:
        """Get detailed information about a specific product.

        Args:
            product_id: Product ID

        Returns:
            Product details dictionary

        Raises:
            ValueError: If product_id is not provided
            RuntimeError: If catalog call fails after retries
        """
        if not product_id:
            raise ValueError("product_id must be provided")

        # Check cache
        params = {"product_id": product_id}
        cache_key = self._get_cache_key("get_product_details", params)

        if self.cache_enabled and cache_key in self._cache:
            cached_data, cached_time = self._cache[cache_key]
            if self._is_cache_valid(cached_time):
                self.logger.debug("Cache hit", cache_key=cache_key)
                return cached_data

        try:
            result = await self.catalog_server.call("get_product_details", params)

            # Cache result
            if self.cache_enabled:
                import time

                self._cache[cache_key] = (result, time.time())

            return result
        except Exception as e:
            self.logger.error("Failed to get product details", error=str(e), product_id=product_id)
            raise RuntimeError(f"Failed to get product details: {str(e)}") from e

    @retry_on_error(max_retries=3, delay=1.0, backoff=2.0)
    async def search_products(
        self,
        query: str,
        limit: int = 10,
    ) -> Dict[str, Any]:
        """Search products by name or description.

        Args:
            query: Search query
            limit: Maximum number of results

        Returns:
            Search results dictionary

        Raises:
            ValueError: If query is not provided
            RuntimeError: If catalog call fails after retries
        """
        if not query:
            raise ValueError("query must be provided")

        # Check cache
        params = {"query": query, "limit": limit}
        cache_key = self._get_cache_key("search_products", params)

        if self.cache_enabled and cache_key in self._cache:
            cached_data, cached_time = self._cache[cache_key]
            if self._is_cache_valid(cached_time):
                self.logger.debug("Cache hit", cache_key=cache_key)
                return cached_data

        try:
            result = await self.catalog_server.call("search_products", params)

            # Cache result
            if self.cache_enabled:
                import time

                self._cache[cache_key] = (result, time.time())

            return result
        except Exception as e:
            self.logger.error("Failed to search products", error=str(e), query=query)
            raise RuntimeError(f"Failed to search products: {str(e)}") from e

    def clear_cache(self) -> None:
        """Clear the cache."""
        self._cache.clear()
        self.logger.debug("Cache cleared")

