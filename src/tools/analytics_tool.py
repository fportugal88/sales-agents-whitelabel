"""Analytics Tool for interacting with Analytics MCP server."""

import asyncio
from functools import wraps
from typing import Any, Callable, Dict, Optional

from src.mcp_servers.mock_analytics_server import MockAnalyticsServer
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


class AnalyticsTool(LoggerMixin):
    """Tool for interacting with Analytics MCP server with error handling and retry logic."""

    def __init__(
        self,
        analytics_server: MockAnalyticsServer,
        cache_enabled: bool = True,
        cache_ttl: int = 300,  # Shorter TTL for analytics
        max_retries: int = 3,
        retry_delay: float = 1.0,
        retry_backoff: float = 2.0,
    ) -> None:
        """Initialize analytics tool.

        Args:
            analytics_server: Analytics MCP server instance
            cache_enabled: Whether to enable caching
            cache_ttl: Cache time-to-live in seconds
            max_retries: Maximum retry attempts
            retry_delay: Initial retry delay
            retry_backoff: Retry backoff multiplier
        """
        self.analytics_server = analytics_server
        self.cache_enabled = cache_enabled
        self.cache_ttl = cache_ttl
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.retry_backoff = retry_backoff
        self._cache: Dict[str, tuple[Any, float]] = {}
        self.logger.info("Analytics tool initialized")

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
    async def get_conversion_metrics(
        self,
        stage: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get conversion metrics for a stage or all stages.

        Args:
            stage: Optional stage to filter by
            start_date: Optional start date (ISO format)
            end_date: Optional end date (ISO format)

        Returns:
            Conversion metrics dictionary

        Raises:
            RuntimeError: If analytics call fails after retries
        """
        # Check cache
        params = {"stage": stage, "start_date": start_date, "end_date": end_date}
        cache_key = self._get_cache_key("get_conversion_metrics", params)

        if self.cache_enabled and cache_key in self._cache:
            cached_data, cached_time = self._cache[cache_key]
            if self._is_cache_valid(cached_time):
                self.logger.debug("Cache hit", cache_key=cache_key)
                return cached_data

        try:
            result = await self.analytics_server.call("get_conversion_metrics", params)

            # Cache result
            if self.cache_enabled:
                import time

                self._cache[cache_key] = (result, time.time())

            return result
        except Exception as e:
            self.logger.error(
                "Failed to get conversion metrics",
                error=str(e),
                stage=stage,
                start_date=start_date,
                end_date=end_date,
            )
            raise RuntimeError(f"Failed to get conversion metrics: {str(e)}") from e

    @retry_on_error(max_retries=3, delay=1.0, backoff=2.0)
    async def get_funnel_analytics(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get funnel analytics for all stages.

        Args:
            start_date: Optional start date (ISO format)
            end_date: Optional end date (ISO format)

        Returns:
            Funnel analytics dictionary

        Raises:
            RuntimeError: If analytics call fails after retries
        """
        # Check cache
        params = {"start_date": start_date, "end_date": end_date}
        cache_key = self._get_cache_key("get_funnel_analytics", params)

        if self.cache_enabled and cache_key in self._cache:
            cached_data, cached_time = self._cache[cache_key]
            if self._is_cache_valid(cached_time):
                self.logger.debug("Cache hit", cache_key=cache_key)
                return cached_data

        try:
            result = await self.analytics_server.call("get_funnel_analytics", params)

            # Cache result
            if self.cache_enabled:
                import time

                self._cache[cache_key] = (result, time.time())

            return result
        except Exception as e:
            self.logger.error(
                "Failed to get funnel analytics",
                error=str(e),
                start_date=start_date,
                end_date=end_date,
            )
            raise RuntimeError(f"Failed to get funnel analytics: {str(e)}") from e

    @retry_on_error(max_retries=3, delay=1.0, backoff=2.0)
    async def track_event(
        self,
        event_type: str,
        stage: str,
        lead_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Track an analytics event.

        Args:
            event_type: Type of event
            stage: Pipeline stage
            lead_id: Optional lead ID
            metadata: Optional event metadata

        Returns:
            Tracking result dictionary

        Raises:
            ValueError: If event_type or stage is not provided
            RuntimeError: If analytics call fails after retries
        """
        if not event_type or not stage:
            raise ValueError("event_type and stage must be provided")

        try:
            result = await self.analytics_server.call(
                "track_event",
                {
                    "event_type": event_type,
                    "stage": stage,
                    "lead_id": lead_id,
                    "metadata": metadata or {},
                },
            )

            # Don't cache tracking calls
            return result
        except Exception as e:
            self.logger.error(
                "Failed to track event",
                error=str(e),
                event_type=event_type,
                stage=stage,
                lead_id=lead_id,
            )
            raise RuntimeError(f"Failed to track event: {str(e)}") from e

    def clear_cache(self) -> None:
        """Clear the cache."""
        self._cache.clear()
        self.logger.debug("Cache cleared")

