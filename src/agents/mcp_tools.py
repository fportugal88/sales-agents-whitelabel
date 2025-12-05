"""MCP Tools integration for dynamic tool calls."""

import httpx
from typing import Any, Dict, List, Optional

from src.models.agent_config import MCPTool
from src.utils.logger import LoggerMixin


class MCPTools(LoggerMixin):
    """Manager for MCP tools integration with support for multiple servers."""

    def __init__(
        self,
        tools: List[MCPTool],
        settings: Optional[Any] = None,
        servers: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize MCP tools manager.

        Args:
            tools: List of MCP tool configurations
            settings: Optional settings for MCP URL configuration
            servers: Optional dict of MCP server instances (for direct calls)
        """
        self.tools: Dict[str, MCPTool] = {tool.name: tool for tool in tools}
        self.settings = settings
        self.servers: Dict[str, Any] = servers or {}
        
        # Mock servers don't need SSL verification (they work in-memory)
        self.verify_ssl = True
        
        self.logger.info("MCP tools initialized", tools_count=len(self.tools), servers_count=len(self.servers))

    async def call_tool(
        self,
        tool_name: str,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Call an MCP tool.

        Args:
            tool_name: Name of the tool to call
            parameters: Tool parameters

        Returns:
            Tool response

        Raises:
            ValueError: If tool not found
            RuntimeError: If tool call fails
        """
        if tool_name not in self.tools:
            # Get available tools for better error message
            available_tools = list(self.tools.keys())
            
            # Try to find similar tool names
            similar_tools = []
            tool_name_lower = tool_name.lower()
            for available_tool in available_tools:
                if tool_name_lower in available_tool.lower() or available_tool.lower() in tool_name_lower:
                    similar_tools.append(available_tool)
            
            error_msg = f"Tool '{tool_name}' não encontrada."
            if similar_tools:
                error_msg += f" Tools similares disponíveis: {', '.join(similar_tools[:5])}"
            elif available_tools:
                error_msg += f" Tools disponíveis: {', '.join(available_tools[:10])}"
            else:
                error_msg += " Nenhuma tool disponível."
            
            self.logger.error(
                "Tool não encontrada",
                tool_name=tool_name,
                available_tools_count=len(available_tools),
                similar_tools=similar_tools[:5] if similar_tools else []
            )
            
            raise ValueError(error_msg)

        tool = self.tools[tool_name]
        params = parameters or {}

        # Merge with default parameters if any
        if tool.parameters:
            params = {**tool.parameters, **params}

        self.logger.info(
            "Chamando MCP tool",
            tool_name=tool_name,
            mcp_url=tool.mcp_url,
            parameters=params,
        )

        # Try direct server call first (if server instance available)
        server_name = self._get_server_name_from_url(tool.mcp_url)
        if server_name in self.servers:
            try:
                server = self.servers[server_name]
                result = await server.call(tool_name, params)
                self.logger.info(
                    "MCP tool chamada via servidor direto",
                    tool_name=tool_name,
                    server_name=server_name,
                    success=result.get("success", False),
                )
                return result
            except Exception as e:
                self.logger.warning(
                    "Erro ao chamar via servidor direto, tentando HTTP",
                    tool_name=tool_name,
                    error=str(e),
                )

        # Fallback to HTTP call
        # Get timeout from settings if available
        timeout_value = 30.0
        if self.settings and hasattr(self.settings, 'mcp_timeout'):
            timeout_value = self.settings.mcp_timeout
        
        try:
            async with httpx.AsyncClient(timeout=timeout_value, verify=self.verify_ssl) as client:
                response = await client.post(
                    f"{tool.mcp_url}/mcp/call",
                    json={
                        "tool_name": tool_name,
                        "parameters": params,
                    },
                )
                response.raise_for_status()
                result = response.json()

                self.logger.info(
                    "MCP tool chamada com sucesso",
                    tool_name=tool_name,
                    success=result.get("success", False),
                )

                return result

        except httpx.ConnectError as e:
            self.logger.error(
                "Erro de conexão ao chamar MCP tool",
                tool_name=tool_name,
                mcp_url=tool.mcp_url,
                error=str(e),
                hint="Verifique se o servidor MCP está rodando e acessível"
            )
            raise RuntimeError(
                f"Falha ao conectar com servidor MCP para tool '{tool_name}': {str(e)}\n"
                f"URL: {tool.mcp_url}\n"
                f"Verifique se o servidor MCP está rodando."
            ) from e
        except httpx.TimeoutException as e:
            self.logger.error(
                "Timeout ao chamar MCP tool",
                tool_name=tool_name,
                mcp_url=tool.mcp_url,
                timeout=timeout_value,
                error=str(e)
            )
            raise RuntimeError(
                f"Timeout ao chamar tool '{tool_name}' (timeout: {timeout_value}s). "
                f"O servidor MCP pode estar sobrecarregado ou inacessível."
            ) from e
        except httpx.HTTPStatusError as e:
            self.logger.error(
                "Erro HTTP ao chamar MCP tool",
                tool_name=tool_name,
                mcp_url=tool.mcp_url,
                status_code=e.response.status_code,
                error=str(e),
            )
            raise RuntimeError(
                f"Erro HTTP {e.response.status_code} ao chamar tool '{tool_name}': {str(e)}"
            ) from e
        except httpx.HTTPError as e:
            self.logger.error(
                "Erro HTTP ao chamar MCP tool",
                tool_name=tool_name,
                mcp_url=tool.mcp_url,
                error=str(e),
            )
            raise RuntimeError(f"Falha ao chamar tool {tool_name}: {str(e)}") from e
        except Exception as e:
            self.logger.error(
                "Erro inesperado ao chamar MCP tool",
                tool_name=tool_name,
                mcp_url=tool.mcp_url,
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True
            )
            raise RuntimeError(f"Erro inesperado ao chamar tool {tool_name}: {str(e)}") from e

    def _get_server_name_from_url(self, url: str) -> str:
        """Extract server name from URL.

        Args:
            url: MCP server URL

        Returns:
            Server name
        """
        # Extract server name from URL pattern
        # e.g., http://localhost:8001 -> mock_crm
        # This is a simple heuristic - can be improved
        if "8001" in url:
            return "mock_crm"
        elif "8002" in url:
            return "mock_catalog"
        elif "8003" in url:
            return "mock_analytics"
        elif "8005" in url:
            return "mock_ifood"
        elif "8006" in url:
            return "mock_restaurant"
        elif "8007" in url:
            return "mock_recommendation"
        elif "8008" in url:
            return "mock_contract"
        elif "8009" in url:
            return "mock_pricing"
        elif "8010" in url:
            return "mock_qualification"
        return "unknown"

    async def list_tools(self, mcp_url: Optional[str] = None) -> List[str]:
        """List available tools from MCP server.

        Args:
            mcp_url: Optional MCP server URL (if None, lists all registered tools)

        Returns:
            List of tool names
        """
        if mcp_url:
            # Try direct server call first
            server_name = self._get_server_name_from_url(mcp_url)
            if server_name in self.servers:
                try:
                    server = self.servers[server_name]
                    tools = server.list_tools()
                    return [tool["name"] for tool in tools]
                except Exception as e:
                    self.logger.warning(
                        "Erro ao listar tools via servidor direto",
                        server_name=server_name,
                        error=str(e),
                    )

            # Fallback to HTTP call
            # Use shorter timeout for tool listing
            list_timeout = 10.0
            if self.settings and hasattr(self.settings, 'mcp_timeout'):
                list_timeout = min(self.settings.mcp_timeout, 10.0)  # Cap at 10s for listing
            
            try:
                async with httpx.AsyncClient(timeout=list_timeout, verify=self.verify_ssl) as client:
                    response = await client.get(f"{mcp_url}/mcp/tools")
                    response.raise_for_status()
                    data = response.json()
                    return [tool["name"] for tool in data.get("tools", [])]
            except httpx.ConnectError as e:
                self.logger.warning(
                    "Erro de conexão ao listar tools do MCP",
                    mcp_url=mcp_url,
                    error=str(e),
                    hint="Servidor MCP pode não estar rodando"
                )
                return []
            except httpx.TimeoutException as e:
                self.logger.warning(
                    "Timeout ao listar tools do MCP",
                    mcp_url=mcp_url,
                    timeout=list_timeout,
                    error=str(e)
                )
                return []
            except Exception as e:
                self.logger.warning(
                    "Erro ao listar tools do MCP",
                    mcp_url=mcp_url,
                    error=str(e),
                )
                return []

        # Return registered tools
        return list(self.tools.keys())

    async def discover_tools(self, mcp_url: str) -> List[Dict[str, Any]]:
        """Discover all tools from an MCP server.

        Args:
            mcp_url: MCP server URL

        Returns:
            List of tool definitions
        """
        server_name = self._get_server_name_from_url(mcp_url)
        if server_name in self.servers:
            try:
                server = self.servers[server_name]
                return server.list_tools()
            except Exception as e:
                self.logger.warning(
                    "Erro ao descobrir tools via servidor direto",
                    server_name=server_name,
                    error=str(e),
                )

        # Fallback to HTTP
        # Use shorter timeout for tool discovery
        discover_timeout = 10.0
        if self.settings and hasattr(self.settings, 'mcp_timeout'):
            discover_timeout = min(self.settings.mcp_timeout, 10.0)  # Cap at 10s for discovery
        
        try:
            async with httpx.AsyncClient(timeout=discover_timeout, verify=self.verify_ssl) as client:
                response = await client.get(f"{mcp_url}/mcp/tools")
                response.raise_for_status()
                data = response.json()
                return data.get("tools", [])
        except httpx.ConnectError as e:
            self.logger.warning(
                "Erro de conexão ao descobrir tools do MCP",
                mcp_url=mcp_url,
                error=str(e),
                hint="Servidor MCP pode não estar rodando"
            )
            return []
        except httpx.TimeoutException as e:
            self.logger.warning(
                "Timeout ao descobrir tools do MCP",
                mcp_url=mcp_url,
                timeout=discover_timeout,
                error=str(e)
            )
            return []
        except Exception as e:
            self.logger.warning(
                "Erro ao descobrir tools do MCP",
                mcp_url=mcp_url,
                error=str(e),
            )
            return []

    def get_tool_info(self, tool_name: str) -> Optional[MCPTool]:
        """Get tool configuration.

        Args:
            tool_name: Name of the tool

        Returns:
            Tool configuration or None if not found
        """
        return self.tools.get(tool_name)

    def has_tool(self, tool_name: str) -> bool:
        """Check if tool is available.

        Args:
            tool_name: Name of the tool

        Returns:
            True if tool is available
        """
        return tool_name in self.tools

