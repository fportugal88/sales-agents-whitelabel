"""Factory for creating and managing MCP server instances."""

from typing import Any, Dict, Optional

from src.config.settings import Settings
from src.mcp_servers.base_mcp import BaseMCPServer
from src.mcp_servers.mock_analytics_server import MockAnalyticsServer
from src.mcp_servers.mock_catalog_server import MockCatalogServer
from src.mcp_servers.mock_contract_server import MockContractServer
from src.mcp_servers.mock_crm_server import MockCRMServer
from src.mcp_servers.mock_ifood_server import MockiFoodServer
from src.mcp_servers.mock_pricing_server import MockPricingServer
from src.mcp_servers.mock_qualification_server import MockQualificationServer
from src.mcp_servers.mock_recommendation_server import MockRecommendationServer
from src.mcp_servers.mock_restaurant_server import MockRestaurantServer
from src.utils.logger import LoggerMixin


class MCPServerFactory(LoggerMixin):
    """Factory for creating and managing MCP server instances.
    
    Provides centralized creation and caching of MCP server instances
    to avoid duplication and ensure consistency.
    """

    _instances: Dict[str, BaseMCPServer] = {}
    _settings: Optional[Settings] = None

    @classmethod
    def initialize(cls, settings: Settings) -> None:
        """Initialize factory with settings.
        
        Args:
            settings: Application settings
        """
        cls._settings = settings
        cls._instances.clear()
        factory = cls()
        factory.logger.info("MCP Server Factory inicializado")

    @classmethod
    def get_server(cls, server_name: str, simulate_latency: bool = False) -> BaseMCPServer:
        """Get or create an MCP server instance.
        
        Args:
            server_name: Name of the server (e.g., 'mock_crm', 'mock_catalog')
            simulate_latency: Whether to simulate network latency
            
        Returns:
            MCP server instance
            
        Raises:
            ValueError: If server_name is not recognized
        """
        if cls._settings is None:
            raise RuntimeError("MCPServerFactory not initialized. Call initialize() first.")
        
        # Check cache first
        cache_key = f"{server_name}_{simulate_latency}"
        if cache_key in cls._instances:
            return cls._instances[cache_key]
        
        # Create new instance
        server = cls._create_server(server_name, simulate_latency)
        
        # Cache it
        cls._instances[cache_key] = server
        
        factory = cls()
        factory.logger.info(
            "MCP server criado",
            server_name=server_name,
            simulate_latency=simulate_latency,
        )
        
        return server

    @classmethod
    def get_all_servers(cls, simulate_latency: bool = False) -> Dict[str, BaseMCPServer]:
        """Get all available MCP servers.
        
        Args:
            simulate_latency: Whether to simulate network latency
            
        Returns:
            Dictionary mapping server names to server instances
        """
        server_names = [
            "mock_crm",
            "mock_catalog",
            "mock_analytics",
            "mock_ifood",
            "mock_restaurant",
            "mock_recommendation",
            "mock_contract",
            "mock_pricing",
            "mock_qualification",
        ]
        
        servers = {}
        for name in server_names:
            servers[name] = cls.get_server(name, simulate_latency)
        
        return servers

    @classmethod
    def _create_server(cls, server_name: str, simulate_latency: bool) -> BaseMCPServer:
        """Create a new MCP server instance.
        
        Args:
            server_name: Name of the server
            simulate_latency: Whether to simulate network latency
            
        Returns:
            New MCP server instance
            
        Raises:
            ValueError: If server_name is not recognized
        """
        # All mock servers don't need base_url - they work in-memory
        server_map = {
            "mock_crm": lambda: MockCRMServer(
                base_url=None,
                simulate_latency=simulate_latency,
            ),
            "mock_catalog": lambda: MockCatalogServer(
                base_url=None,
                simulate_latency=simulate_latency,
            ),
            "mock_analytics": lambda: MockAnalyticsServer(
                base_url=None,
                simulate_latency=simulate_latency,
            ),
            "mock_ifood": lambda: MockiFoodServer(
                simulate_latency=simulate_latency,
            ),
            "mock_restaurant": lambda: MockRestaurantServer(
                simulate_latency=simulate_latency,
            ),
            "mock_recommendation": lambda: MockRecommendationServer(
                simulate_latency=simulate_latency,
            ),
            "mock_contract": lambda: MockContractServer(
                simulate_latency=simulate_latency,
            ),
            "mock_pricing": lambda: MockPricingServer(
                simulate_latency=simulate_latency,
            ),
            "mock_qualification": lambda: MockQualificationServer(
                simulate_latency=simulate_latency,
            ),
        }
        
        if server_name not in server_map:
            raise ValueError(
                f"Unknown server name: {server_name}. "
                f"Available: {', '.join(server_map.keys())}"
            )
        
        return server_map[server_name]()

    @classmethod
    def clear_cache(cls) -> None:
        """Clear the server instance cache."""
        cls._instances.clear()
        factory = cls()
        factory.logger.info("Cache de MCP servers limpo")

