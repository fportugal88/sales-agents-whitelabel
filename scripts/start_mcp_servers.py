"""Script to start MCP HTTP servers."""

import asyncio

from src.config.settings import get_settings
from src.mcp_servers.http_server import start_mcp_servers
from src.mcp_servers.mock_analytics_server import MockAnalyticsServer
from src.mcp_servers.mock_catalog_server import MockCatalogServer
from src.mcp_servers.mock_crm_server import MockCRMServer
from src.utils.logger import configure_logging


async def main():
    """Start MCP servers."""
    configure_logging()
    settings = get_settings()

    # Create MCP servers
    crm_server = MockCRMServer(
        base_url=settings.mcp_crm_server_url,
        simulate_latency=False,
    )
    catalog_server = MockCatalogServer(
        base_url=settings.mcp_catalog_server_url,
        simulate_latency=False,
    )
    analytics_server = MockAnalyticsServer(
        base_url=settings.mcp_analytics_server_url,
        simulate_latency=False,
    )

    # Start HTTP servers
    servers = await start_mcp_servers(crm_server, catalog_server, analytics_server)

    print("=" * 60)
    print("MCP Servers started successfully!")
    print("=" * 60)
    print(f"  - CRM Server: http://localhost:8001")
    print(f"  - Catalog Server: http://localhost:8002")
    print(f"  - Analytics Server: http://localhost:8003")
    print("\nEndpoints:")
    print("  - POST http://localhost:8001/mcp/call")
    print("  - GET  http://localhost:8001/mcp/tools")
    print("  - GET  http://localhost:8001/health")
    print("\nPress Ctrl+C to stop...")
    print("=" * 60)

    try:
        # Keep servers running
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        print("\nStopping servers...")
        for server in servers:
            await server.stop()
        print("Servers stopped.")


if __name__ == "__main__":
    asyncio.run(main())

