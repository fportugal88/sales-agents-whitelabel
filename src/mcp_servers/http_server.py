"""HTTP server for MCP servers."""

from typing import Any, Dict, Optional

from aiohttp import web
from aiohttp.web_request import Request
from aiohttp.web_response import Response

from src.mcp_servers.base_mcp import BaseMCPServer
from src.utils.logger import LoggerMixin


class MCPServerHTTP(LoggerMixin):
    """HTTP server wrapper for MCP servers."""

    def __init__(self, mcp_server: BaseMCPServer, port: int) -> None:
        """Initialize HTTP server for MCP.

        Args:
            mcp_server: MCP server instance
            port: Port to run server on
        """
        self.mcp_server = mcp_server
        self.port = port
        self.app = web.Application()
        self.runner: Optional[web.AppRunner] = None
        self._setup_routes()
        self.logger.info(
            "MCP HTTP server initialized", port=port, server_name=mcp_server.server_name
        )

    def _setup_routes(self) -> None:
        """Setup HTTP routes."""
        self.app.router.add_post("/mcp/call", self.handle_call)
        self.app.router.add_get("/mcp/tools", self.handle_list_tools)
        self.app.router.add_get("/health", self.handle_health)

    async def handle_call(self, request: Request) -> Response:
        """Handle MCP tool call.

        Args:
            request: HTTP request

        Returns:
            HTTP response
        """
        try:
            data = await request.json()
            tool_name = data.get("tool_name")
            parameters = data.get("parameters", {})

            if not tool_name:
                return web.json_response({"error": "tool_name is required"}, status=400)

            result = await self.mcp_server.call(tool_name, parameters)
            return web.json_response(result)

        except Exception as e:
            self.logger.error("Error handling MCP call", error=str(e))
            return web.json_response({"error": str(e)}, status=500)

    async def handle_list_tools(self, request: Request) -> Response:
        """Handle list tools request.

        Args:
            request: HTTP request

        Returns:
            HTTP response
        """
        try:
            tools = self.mcp_server.list_tools()
            return web.json_response({"tools": tools})
        except Exception as e:
            self.logger.error("Error listing tools", error=str(e))
            return web.json_response({"error": str(e)}, status=500)

    async def handle_health(self, request: Request) -> Response:
        """Handle health check.

        Args:
            request: HTTP request

        Returns:
            HTTP response
        """
        return web.json_response(
            {"status": "healthy", "server": self.mcp_server.server_name}
        )

    async def start(self) -> None:
        """Start the HTTP server."""
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        site = web.TCPSite(self.runner, "localhost", self.port)
        await site.start()
        self.logger.info(f"MCP HTTP server started on port {self.port}")

    async def stop(self) -> None:
        """Stop the HTTP server."""
        if self.runner:
            await self.runner.cleanup()
        self.logger.info(f"MCP HTTP server stopped on port {self.port}")


async def start_mcp_servers(
    crm_server: BaseMCPServer,
    catalog_server: BaseMCPServer,
    analytics_server: BaseMCPServer,
) -> list[MCPServerHTTP]:
    """Start all MCP HTTP servers.

    Args:
        crm_server: CRM MCP server
        catalog_server: Catalog MCP server
        analytics_server: Analytics MCP server

    Returns:
        List of running HTTP servers
    """
    servers = [
        MCPServerHTTP(crm_server, 8001),
        MCPServerHTTP(catalog_server, 8002),
        MCPServerHTTP(analytics_server, 8003),
    ]

    for server in servers:
        await server.start()

    return servers

