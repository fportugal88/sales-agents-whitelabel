"""Mock MCP servers."""

from src.mcp_servers.base_mcp import BaseMCPServer
from src.mcp_servers.mock_analytics_server import MockAnalyticsServer
from src.mcp_servers.mock_catalog_server import MockCatalogServer
from src.mcp_servers.mock_crm_server import MockCRMServer

__all__ = [
    "BaseMCPServer",
    "MockCRMServer",
    "MockCatalogServer",
    "MockAnalyticsServer",
]
